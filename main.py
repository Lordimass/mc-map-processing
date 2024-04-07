import anvil
import os
import numpy as np
import PIL.Image as PILage

import osFunctions
import realise

REGIONS_DIRECTORY = "region"
REGION_BOUNDS = [ # Inclusive
    [-5,-1], # Top left corner
    [1,5]  # Bottom right corner
]
BORDER_CENTRE = (-625//16, 1559//16)
BORDER_DIAMETER = 2000//16

def int_atr(object, attribute):
    return int(str(object.data[attribute]))

# Check whether REGIONS_DIRECTORY exists, if not create it and prompt user to upload files
regionsExist = osFunctions.check_for_directory(REGIONS_DIRECTORY, 
                                               fail_response = "No regions directory found, please upload your .mca files to the '{REGIONS_DIRECTORY}' directory, then restart the program.")
if regionsExist:
    if os.listdir(REGIONS_DIRECTORY) == []:
        osFunctions.quit(f"No regions found in '{REGIONS_DIRECTORY}', please upload at least one .mca file and try again")
else:
    osFunctions.quit("")

# Removes additional syntax from the file name of a region, returning a tuple of values
def get_region_coords_from_file_name(filename):
    regionCoordinates = filename.rstrip(".mca").lstrip("r.").split(".")

    for coordinate in [0,1]:
        regionCoordinates[coordinate] = int(regionCoordinates[coordinate])
    
    return tuple(regionCoordinates)

# Creating suitably sized array of Tuples which can be later converted to an image
regionFileNames = []
xRange = [0,0]
zRange = [0,0]
for regionFileName in os.listdir(REGIONS_DIRECTORY):
    regionFileNames.append(regionFileName)
    regionCoordinates = get_region_coords_from_file_name(regionFileName)

    xRange[0] = min(regionCoordinates[0], xRange[0])
    xRange[1] = max(regionCoordinates[1], xRange[1])
    zRange[0] = min(regionCoordinates[0], zRange[0])
    zRange[1] = max(regionCoordinates[1], zRange[1])

#xRange[0] = min(xRange[0], REGION_BOUNDS[0][0])
#xRange[1] = max(xRange[1], REGION_BOUNDS[1][0])
#zRange[0] = min(zRange[0], REGION_BOUNDS[0][1])
#zRange[1] = max(zRange[1], REGION_BOUNDS[1][1])

xRange[0] = REGION_BOUNDS[0][0]
xRange[1] = REGION_BOUNDS[1][0]+1
zRange[0] = REGION_BOUNDS[0][1]
zRange[1] = REGION_BOUNDS[1][1]+1

xRangeMagnitude = xRange[1] - xRange[0] # Calculating the magnitude of the range of possible values 
zRangeMagnitude = zRange[1] - zRange[0] # which determines the size of the image

chunkData = np.zeros((32*xRangeMagnitude,32*zRangeMagnitude, 3), dtype=np.uint8)
print(f"Image output will be {len(chunkData[0])}x{len(chunkData)}")

# Reading Data From Region
maxInhabitedTime = 0
for regionFileName in regionFileNames:
    regionCoordinates = get_region_coords_from_file_name(regionFileName)

    # Filtering out results outside of the bounds of the map
    xValid = REGION_BOUNDS[0][0] <= regionCoordinates[0] <= REGION_BOUNDS[1][0]
    zValid = REGION_BOUNDS[0][1] <= regionCoordinates[1] <= REGION_BOUNDS[1][1]
    if not(xValid) or not(zValid):
        continue

    print(f"Scanning region {regionFileName}")
    regionFilePath = REGIONS_DIRECTORY + "/" + regionFileName
    region = anvil.Region.from_file(regionFilePath)
    for relChunkX in range(0,32):
        for relChunkZ in range(0,32):
            try:
                chunk = region.get_chunk(relChunkX, relChunkZ)
                maxInhabitedTime = max(maxInhabitedTime, int_atr(chunk, "InhabitedTime"))
            except:
                chunk = None
                continue

            realChunkCoord = realise.realise_chunk(regionCoordinates, [relChunkX, relChunkZ])  
            try: # Some chunks overhang outside the map area, cull them.
                value = (int_atr(chunk, "InhabitedTime")/19684776 + 0.01)*255 

                chunkData[
                    realChunkCoord[0] - xRange[0]*32,
                    realChunkCoord[1] - zRange[0]*32
                  ] = [value, value, value]
            except:
                pass

print(maxInhabitedTime)


# Highlighting World Border
centre = (BORDER_CENTRE[0] - xRange[0]*32, BORDER_CENTRE[1] - zRange[0]*32)
print(centre)
for z in range(len(chunkData)):
    for x in range(len(chunkData[0])):
        xHighlight = not(centre[0] - (BORDER_DIAMETER//2) <= x <= centre[0] + (BORDER_DIAMETER//2))
        zHighlight = not(centre[1] - (BORDER_DIAMETER//2) <= z <= centre[1] + (BORDER_DIAMETER//2))
        if xHighlight or zHighlight:
            chunkData[z,x][0] = 255/4

chunkData[centre[0],centre[1]] = (255,0,0)

# Colour based on inhabited time
'''for chunk in chunks:
    pxX = int_atr(chunk, "xPos") - xRange[0]*32
    pxY = int_atr(chunk, "yPos") - zRange[0]*32
    if pxX % 100 == 0 and pxY % 100 == 0:
        print(int_atr(chunk, "InhabitedTime"))
    try:
        chunkData[pxX][pxY][1] = (int_atr(chunk, "InhabitedTime") / maxInhabitedTime) * 255
    except:
        #print(e)
        pass
    #print(chunkData[pxX][pxY][1])'''

# Converting data to an image

img = PILage.fromarray(chunkData, mode="RGB")
img.show()
img.save("output.png")
