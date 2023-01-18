# Updated:
#  - now processes HWRM background "LITE[]" joints (creates a lamp)
#  - now processes HWRM "MAT[xx]_PARAM[yy]" joints (creates a joint with custom properties)
#  - textures now set to "phong" not "cooktorr"
# Dom2 - 21-SEP-2018
#

# To do:
# [ ] Apply SUB_PARAMS for dock paths
# [o] Implementation of import options:
#         - Import mesh only
# [ ] Remove "_ncl1" tags - is this a good idea?
#
#
# [o] = implemented, not confirmed
# [x] = tested, complete
#

import os,sys
import xml.etree.ElementTree
import math
import mathutils
import bpy
from pathlib import Path

ET = xml.etree.ElementTree

def pause():
    programPause = input("Press the <ENTER> key to continue...")
###############################################################################
# TEST CASE SUMMARY
###############################################################################

# Gearbox examples
# Kad_Swarmer.dae"                        # ok
# Tur_P1Mothership.dae"          # ok
# Kad_Swarmer_local.dae"                # ok
# Kad_FuelPod.DAE"                        # ok
# Tai_Interceptor.DAE"            # ok (badge not checked)
# Tai_MultiGunCorvette.DAE"      # ok (badge not checked)
# Hgn_Carrier.dae"                        # ok when split normals turned off
# Asteroid_3.dae"                          # ok
# Kus_SupportFrigate.dae"          # ok
# planetexample_Light.DAE"        # ok
# Example_light.DAE"                    # ok

# RODOH examples
# meg_gehenna_2.dae"                    # ok
# hgn_shipyard.dae"                      # ok when split normals turned off - flames come in with no parents..
# hgn_battlecruiser.dae          # internal error setting array - subMesh.from_pydata(Verts,[],faceTris)
# hgn_gunturret.dae"                    # internal error setting array - subMesh.from_pydata(Verts,[],faceTris)
# hgn_torpedofrigate.dae"          # ok when split normals turned off
# meg_bentus.dae"                          # OK
# vgr_carrier.dae"                        # ok when split normals turned off
# vgr_mothership.dae"              # ok when split normals turned off

# Blender-generated TRP ships
# trp_marinefrigate.dae"                # ok
# trp_assaultfrigate.dae"          # ok
# trp_ioncannonfrigate.dae"      # ok

# 3DSMax-generated TRP ships
# trp_resourcecollector.DAE"    # ok
# trp_carrier.DAE"                        # ok
# trp_assaultcorvette.DAE"        # ok
# trp_probe.DAE"                                # ok
# trp_interceptor.DAE"            # ok
# trp_scout.DAE"                                # ok
# trp_attackbomber.DAE"          # ok
# trp_sensdisprobe.DAE            # ok
# trp_proximitysensor.DAE          # ok

###############################################################################
###############################################################################
###############################################################################

#############
#DAE Schemas#
#############

#Just defining all the DAE attributes here so the processing functions are more easily readable

#Asset Schemas
DAEUpAxis = "{http://www.collada.org/2005/11/COLLADASchema}up_axis"

#Utility Schemas
DAENode = "{http://www.collada.org/2005/11/COLLADASchema}node"
DAETranslation = "{http://www.collada.org/2005/11/COLLADASchema}translate"
DAEInit = "{http://www.collada.org/2005/11/COLLADASchema}init_from"
DAEInput = "{http://www.collada.org/2005/11/COLLADASchema}input"
DAEFloats = "{http://www.collada.org/2005/11/COLLADASchema}float_array"
DAESource = "{http://www.collada.org/2005/11/COLLADASchema}source"
DAEInstance = "{http://www.collada.org/2005/11/COLLADASchema}instance_geometry"

#Material Schemas
DAELibMaterials = "{http://www.collada.org/2005/11/COLLADASchema}library_materials"
DAEMaterials = "{http://www.collada.org/2005/11/COLLADASchema}material"
DAELibEffects = "{http://www.collada.org/2005/11/COLLADASchema}library_effects"
DAEfx = "{http://www.collada.org/2005/11/COLLADASchema}effect"
DAELibImages = "{http://www.collada.org/2005/11/COLLADASchema}library_images"
DAEimage = "{http://www.collada.org/2005/11/COLLADASchema}image"
DAEDiff = "{http://www.collada.org/2005/11/COLLADASchema}diffuse"
DAETex = "{http://www.collada.org/2005/11/COLLADASchema}texture"
DAEProfile = "{http://www.collada.org/2005/11/COLLADASchema}profile_COMMON"
DAETechnique = "{http://www.collada.org/2005/11/COLLADASchema}technique"
DAEPhong = "{http://www.collada.org/2005/11/COLLADASchema}phong"

#Geometry Schemas
DAEGeo = "{http://www.collada.org/2005/11/COLLADASchema}geometry"
DAEMesh = "{http://www.collada.org/2005/11/COLLADASchema}mesh"
DAEVerts = "{http://www.collada.org/2005/11/COLLADASchema}vertices"
DAETris = "{http://www.collada.org/2005/11/COLLADASchema}triangles"
DAEp = "{http://www.collada.org/2005/11/COLLADASchema}p"

#Animation Schemas
DAELibAnims = "{http://www.collada.org/2005/11/COLLADASchema}library_animations"
DAEAnim = "{http://www.collada.org/2005/11/COLLADASchema}animation"
DAEChannel = "{http://www.collada.org/2005/11/COLLADASchema}channel"

###########
#Functions#
###########

def makeTextures(name, DAEPath, path):
    name = name.rstrip("-image")
    # Sort out the image path (it could be absolute, local or relative)
    print("makeTextures()")
    print("************************************************")
    DAEPath = DAEPath + "/"
    print(DAEPath)
    print("Image path from DAE file:")
    print(path)
    if "\\" in DAEPath:
        print("Found \\ in DAEPath!")
        DAEPath = DAEPath.replace("\\","/")
    if "\\" in path:
        print("Found \\ in path!")
        path = path.replace("\\","/")
        print(path)
    if "/" in path:
        if ".." in path:
            print("This is a relative path...")
            DAEPath_elements = DAEPath.split("/")
            print(DAEPath_elements)
            del DAEPath_elements[-1]
            print(DAEPath_elements)
            path_elements = path.split("/")
            print(path_elements)
            for i in path_elements:
                if i == "..":
                    del DAEPath_elements[-1]
            image_path = ""
            print("Building full path...")
            print("-----------")
            for j in DAEPath_elements:
                image_path = image_path + j + "/"
                print(image_path)
            for k in path_elements:
                if k != ".." and k != ".":
                    print(image_path)
                    print(len(image_path))
                    if image_path[len(image_path)-1] != "/":
                        image_path = image_path + "/" + k
                        print('image_path + "/" + k',image_path)
                    else:
                        image_path = image_path + k
                        print('image_path + k',image_path)
            print("-----------")
        else:
            if path.startswith("./"):
                print("This is a local path with ./")
                image_path = DAEPath + path[2:]
            else:
                print("This is an absolute path")
                image_path = path
    else:
        image_path = DAEPath + "/" + path
        # image_path = DAEPath + path #rep_seb
        print("This is a file name only: \n\t Path: ",image_path)
    # Now we have an image path ready to load
    print("Processed image path:")
    print(image_path)

    # But sometimes it is not the DIFF (e.g. Kad_Swarmer)...
    # So correct the image file name
    if "DIFF" not in image_path:
        print("switching file name to DIFF...")
        image_path = image_path[0:len(image_path)-8] + "DIFF" + ".tga"
        print(image_path)
    print(name)
    # And correct the image name (IMG[xxx_DIFF]_FMT[...)
    if "DIFF" not in name:
        print("switching image name to DIFF...")
        # This is a lazy way of doing it, but it works - may no longer be necessary (Dom2 28-NOV-2016)
        name = name.replace("_DIFX]","_DIFF]")
        name = name.replace("_GLOW]","_DIFF]")
        name = name.replace("_GLOX]","_DIFF]")
        name = name.replace("_NORM]","_DIFF]")
        name = name.replace("_PAIN]","_DIFF]")
        name = name.replace("_REFL]","_DIFF]")
        name = name.replace("_REFX]","_DIFF]")
        name = name.replace("_SPEC]","_DIFF]")
        name = name.replace("_SPEX]","_DIFF]")
        name = name.replace("_STRP]","_DIFF]")
        name = name.replace("_TEAM]","_DIFF]")
        print(name)
    # Now get the image
    bpy.data.textures.new(name, 'IMAGE')
    bpy.data.textures[name].image = bpy.data.images.load(image_path)
    image_file_name = image_path.split("/")[len(image_path.split("/"))-1]
    print(image_file_name)
    bpy.data.images[image_file_name].name = name
    print("************************************************")

def makeMaterials(name, textures):
    # bpy.data.materials.new(name) # rep_old
    new_mat = bpy.data.materials.new(name) # seb
    new_mat.use_nodes = True # seb

    if len(textures) > 0:
        print("Material in Make_Material",bpy.data.materials[name]) # seb
        #bpy.data.materials[name].specular_shader = 'PHONG' # dep_old
        bpy.context.object.active_material = new_mat
        #bpy.data.materials[name].texture_slots.add() # dep_old

        texture_name = textures[0]
        if "_DIFF" not in texture_name:
            print("!- makeMaterials() could not find '_DIFF' in texture_name: " + texture_name)
            texture_name = texture_name.replace("_DIFX]","_DIFF]")
            texture_name = texture_name.replace("_GLOW]","_DIFF]")
            texture_name = texture_name.replace("_GLOX]","_DIFF]")
            texture_name = texture_name.replace("_NORM]","_DIFF]")
            texture_name = texture_name.replace("_PAIN]","_DIFF]")
            texture_name = texture_name.replace("_REFL]","_DIFF]")
            texture_name = texture_name.replace("_REFX]","_DIFF]")
            texture_name = texture_name.replace("_SPEC]","_DIFF]")
            texture_name = texture_name.replace("_SPEX]","_DIFF]")
            texture_name = texture_name.replace("_STRP]","_DIFF]")
            texture_name = texture_name.replace("_TEAM]","_DIFF]")
            print("!- makeMaterials() tried to fix it, now using: " + texture_name)
        #bpy.data.materials[name].texture_slots[0].texture = bpy.data.textures[texture_name] # susp
    else:
        print("!- makeMaterials() was given an empty list of textures for mat " + name)

def meshBuilder(matName, Verts, Normals, UVCoords, vertOffset, normOffset, UVoffsets, pArray, smooth):
    print("meshBuilder() - Building "+matName)
    print(UVoffsets)
    subMesh = bpy.data.meshes.new(matName) # Just the plain mesh
    ob = bpy.data.objects.new(subMesh.name, subMesh)
    col = bpy.data.collections.get("Collection")

    #split <p> array to get just the face data
    faceIndices = []
    for i in range(0, len(pArray)):
        faceIndices.append(pArray[i][vertOffset])
    faceTris = [faceIndices[i:i+3] for i in range(0,len(faceIndices),3)]
    subMesh.from_pydata(Verts,[],faceTris)
    #if matName is not "None": # old
    if matName != "None": # seb
        print("meshBuilder() - appending material '" + matName + "' to submesh '" + subMesh.name + "'")
        subMesh.materials.append(bpy.data.materials[matName.lstrip("#")]) # rep_old


    if smooth:
        normIndices = []
        for i in range(0, len(pArray)):
            this_norm_index = mathutils.Vector(Normals[pArray[i][normOffset]])
            normIndices.append(this_norm_index) # This line causes problems for some DAEs, not yet traced why (Dom2 28-NOV-2016)

        print("Splitting normals...")
        subMesh.normals_split_custom_set(normIndices)
    print("Smoothing mesh...")
    subMesh.use_auto_smooth = True

    print("Adding UVs... to mesh: ",subMesh)
    #Add UVs
    if len(UVCoords) > 0 :
        for coords in range(0,len(UVoffsets)):
            #subMesh.uv_textures.new() # old
            subMesh.uv_layers.new()
            meshUV = []
            for p in range(0, len(pArray)):
                meshUV.append(UVCoords[coords][pArray[p][UVoffsets[coords]]])

            for l in range(0,len(subMesh.uv_layers[coords].data)):
                subMesh.uv_layers[coords].data[l].uv = meshUV[l]

    print("Linking objects...")
    # bpy.context.scene.objects.link(ob) # old

    col.objects.link(ob) # seb
    return ob


def ImportDAE(DAEfullpath, smoothing_opt, dock_opt, goblins_opt):
    tree = ET.parse(DAEfullpath)
    root = tree.getroot()

    DAE_file_path = os.path.dirname(DAEfullpath)

    # if up axis = Y and ROOT_LOD[0] has no X rotation, need to rotate about X by 90...
    y_up = False
    for axis in root.iter(DAEUpAxis): # find all <up_axis> in the file
        if axis.text == "Y_UP":
            for n in root.iter(DAENode): # find all <node> in the file
                if "ROOT_LOD[0]" in n.attrib["name"]:
                    for par in n:
                        if "rotate" in par.tag:
                            if "sid" in par.attrib: # sometimes there are "dummy" <rotate> tags with no "sid"... (-pivot, from 3DSMax)
                                if "rotateX" in par.attrib["sid"]:
                                    if float(par.text.split()[3]) < 89:
                                        print("This is probably a RODOH dae - Y axis = up and there is no x rotation on ROOT_LOD[0]")
                                        y_up = True

    #My code starts here - DL

    for geo in root.iter(DAEGeo):
        meshName = geo.attrib["name"] ; print ("Nome Mesh:  ", meshName)
        mesh = geo.find(DAEMesh)

        blankMesh = bpy.data.meshes.new(meshName)
        ob = bpy.data.objects.new(meshName, blankMesh)
        col = bpy.data.collections.get("Collection")
        col.objects.link(ob)

        #print(meshName)

        UVs = []

        for source in mesh.iter(DAESource):
            print("\tSource found:",source.attrib["id"])
            if "position" in source.attrib["id"].lower():
                rawVerts = [float(i) for i in source.find(DAEFloats).text.split()]

            if "normal" in source.attrib["id"].lower():
                rawNormals = [float(i) for i in source.find(DAEFloats).text.split()]

            if "uv" in source.attrib["id"].lower():
                rawUVs = [float(i) for i in source.find(DAEFloats).text.split()]
                coords = [rawUVs[i:i+2] for i in range(0, len(rawUVs),2)]
                UVs.append(coords)

        vertPositions = [rawVerts[i:i+3] for i in range(0, len(rawVerts),3)]
        meshNormals = [rawNormals[i:i+3] for i in range(0, len(rawNormals),3)]

        #print("VertPositions");[print(vert_pos) for vert_pos in vertPositions]
        #print("MeshNormals");[print(norm_pos) for norm_pos in meshNormals]
        #print("223 UVs:",UVs, sep="\n")
        if vertPositions:
            print("Vert Positions : [OK]")
        if meshNormals:
            print("Mesh Normals : [OK]")
        if UVs:
            print("UVs : [OK]")

        subMeshes = []
        material = "None" # seb

        for tris in mesh.iter(DAETris):
            if "material" in tris.attrib:
                material = tris.attrib["material"]
                print("Found <triangles> with material " + material)
            else:
                print("material NOT Founded in:",tris)
                material = "None"

            maxOffset = 0
            UVOffsets = []
            vertOffset = 0
            normOffset = 0
            for inp in tris.iter(DAEInput):
                if int(inp.attrib["offset"]) > maxOffset:
                    maxOffset = int(inp.attrib["offset"])
                if inp.attrib["semantic"].lower() == "texcoord":
                    UVOffsets.append(int(inp.attrib["offset"]))
                if inp.attrib["semantic"].lower() == "vertex":
                    vertOffset = int(inp.attrib["offset"])
                if inp.attrib["semantic"].lower() == "normal":
                    normOffset =  int(inp.attrib["offset"])
            if tris.find(DAEp).text is not None:
                splitPsoup = [int(i) for i in tris.find(DAEp).text.split()]
                pArray = [splitPsoup[i:i+(maxOffset+1)] for i in range(0, len(splitPsoup),(maxOffset+1))]
                # Only build the submesh if it actually has triangles
                subMeshes.append(meshBuilder(material, vertPositions, meshNormals, UVs, vertOffset, normOffset, UVOffsets, pArray, smoothing_opt))
                            #def meshBuilder(matName,  Verts,          Normals,    UVCoords, vertOffset, normOffset, UVoffsets, pArray, smooth):
                print("subMeshes",subMeshes)
        #Combines the material submeshes into one mesh
        # https://blender.stackexchange.com/questions/141330/problem-with-bpy-context-selected-objects
        for obs in subMeshes:
            print("Obs:",obs)
            #bpy.context.view_layer.objects.active = obs # seb
            # obs.select = True # old
            obs.select_set(True) # seb
        #ob.select = True #>
        obs.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.join()
        ob.data.use_auto_smooth = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.editmode_toggle()
        #ob.select = False #>
        obs.select_set(False)













def OLD_ImportDAE(DAEfullpath, smoothing_opt, dock_opt, goblins_opt):
    tree = ET.parse(DAEfullpath)
    root = tree.getroot()

    DAE_file_path = os.path.dirname(DAEfullpath)

    # if up axis = Y and ROOT_LOD[0] has no X rotation, need to rotate about X by 90...
    y_up = False
    for axis in root.iter(DAEUpAxis): # find all <up_axis> in the file
        if axis.text == "Y_UP":
            for n in root.iter(DAENode): # find all <node> in the file
                if "ROOT_LOD[0]" in n.attrib["name"]:
                    for par in n:
                        if "rotate" in par.tag:
                            if "sid" in par.attrib: # sometimes there are "dummy" <rotate> tags with no "sid"... (-pivot, from 3DSMax)
                                if "rotateX" in par.attrib["sid"]:
                                    if float(par.text.split()[3]) < 89:
                                        print("This is probably a RODOH dae - Y axis = up and there is no x rotation on ROOT_LOD[0]")
                                        y_up = True

    print(" ")
    print("CREATING JOINTS")
    print(" ")

    #My code starts here - DL

    #find textures and create them
    for img in root.find(DAELibImages):
        # We use attrib["id]" here because RODOH DAEs have "name"s that do not match their "id"s
        #  this means we will lose the _FMT[] tag but we will have to live with that for now...
        #
        # Example (to solve we would need to add the _FMT[] tag back on at the <texture> stage:
        # <image id="IMG[Hgn_MarineFrigate_Front_DIFF]-image" name="IMG[Hgn_MarineFrigate_Front_DIFF]_FMT[DXT5]">
        # <texture texture="IMG[Hgn_MarineFrigate_Front_DIFF]-image">
        #
        # Let's have a warning message just to let the user know:
        if img.attrib["id"].rstrip("-image") != img.attrib["name"]:
            print("This appears to be a RODOH DAE. _FMT[] tags will be lost from textures - sorry!")
        makeTextures(img.attrib["id"],DAE_file_path,img.find(DAEInit).text.lstrip("file://"))

    #Make materials based on the Effects library
    for fx in root.find(DAELibEffects).iter(DAEfx):
        matname = fx.attrib["name"]
        matTextures = []

        # Just look for the <diffuse> tag - don't care about the other image files
        for d in fx.iter(DAEDiff):
            t = d.find(DAETex)
            print(d)
            print(d.tag)
            if t is not None:
                matTextures.append(t.attrib["texture"].rstrip("-image"))
            # !- may not need to do replacing "DIFF" now... -!

        makeMaterials(matname, matTextures)
    #Find the mesh data and split the coords into 2D arrays

    for geo in root.iter(DAEGeo):
        meshName = geo.attrib["name"] ; print ("Nome Mesh", meshName)
        mesh = geo.find(DAEMesh)

        blankMesh = bpy.data.meshes.new(meshName)
        ob = bpy.data.objects.new(meshName, blankMesh)
        col = bpy.data.collections.get("Collection")
        col.objects.link(ob)

        #print(meshName)

        UVs = []

        for source in mesh.iter(DAESource):
            print("Source found:",source)
            if "position" in source.attrib["id"].lower():
                rawVerts = [float(i) for i in source.find(DAEFloats).text.split()]

            if "normal" in source.attrib["id"].lower():
                rawNormals = [float(i) for i in source.find(DAEFloats).text.split()]

            if "uv" in source.attrib["id"].lower():
                rawUVs = [float(i) for i in source.find(DAEFloats).text.split()]
                coords = [rawUVs[i:i+2] for i in range(0, len(rawUVs),2)]
                UVs.append(coords)

        vertPositions = [rawVerts[i:i+3] for i in range(0, len(rawVerts),3)]
        meshNormals = [rawNormals[i:i+3] for i in range(0, len(rawNormals),3)]

        #print("VertPositions");[print(vert_pos) for vert_pos in vertPositions]
        #print("MeshNormals");[print(norm_pos) for norm_pos in meshNormals]
        #print("223 UVs:",UVs, sep="\n")
        if vertPositions:
            print("Vert Positions : [OK]")
        if meshNormals:
            print("Mesh Normals : [OK]")
        if UVs:
            print("UVs : [OK]")

        subMeshes = []
        material = "None" # seb

        for tris in mesh.iter(DAETris):
            print("tris",tris)
            if "material" in tris.attrib:
                material = tris.attrib["material"]
                print("Found <triangles> with material " + material)
            else:
                print("material NOT Founded in:",tris)
                material = "None"

            maxOffset = 0
            UVOffsets = []
            vertOffset = 0
            normOffset = 0
            for inp in tris.iter(DAEInput):
                if int(inp.attrib["offset"]) > maxOffset:
                    maxOffset = int(inp.attrib["offset"])
                if inp.attrib["semantic"].lower() == "texcoord":
                    UVOffsets.append(int(inp.attrib["offset"]))
                if inp.attrib["semantic"].lower() == "vertex":
                    vertOffset = int(inp.attrib["offset"])
                if inp.attrib["semantic"].lower() == "normal":
                    normOffset =  int(inp.attrib["offset"])
            if tris.find(DAEp).text is not None:
                splitPsoup = [int(i) for i in tris.find(DAEp).text.split()]
                pArray = [splitPsoup[i:i+(maxOffset+1)] for i in range(0, len(splitPsoup),(maxOffset+1))]
                # Only build the submesh if it actually has triangles
                subMeshes.append(meshBuilder(material, vertPositions, meshNormals, UVs, vertOffset, normOffset, UVOffsets, pArray, smoothing_opt))
                            #def meshBuilder(matName,  Verts,          Normals,    UVCoords, vertOffset, normOffset, UVoffsets, pArray, smooth):
                print("subMeshes",subMeshes)
        #Combines the material submeshes into one mesh
        # https://blender.stackexchange.com/questions/141330/problem-with-bpy-context-selected-objects
        for obs in subMeshes:
            print("Obs:",obs)
            #bpy.context.view_layer.objects.active = obs # seb
            # obs.select = True # old
            obs.select_set(True) # seb
        #ob.select = True #>
        obs.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.join()
        ob.data.use_auto_smooth = True
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.remove_doubles()
        bpy.ops.object.editmode_toggle()
        #ob.select = False #>
        obs.select_set(False)

def ImportLOD0(DAEfullpath, smoothing_opt):
    tree = ET.parse(DAEfullpath)
    root = tree.getroot()

    if "\\" in DAEfullpath:
        LOD0Name_ent = DAEfullpath.rstrip("dae").rstrip("DAE").rstrip(".").split("\\")
    else:
        LOD0Name_ent = DAEfullpath.rstrip("dae").rstrip("DAE").rstrip(".").split("\\")
        print(LOD0Name_ent)

    LOD0Name = LOD0Name_ent[len(LOD0Name_ent)-1]

    print("Importing LOD[0] mesh(es) only...")
    print(LOD0Name)

    #Find the mesh data and split the coords into 2D arrays

    LOD0_mesh = 0

    for geo in root.iter(DAEGeo):
        if "MULT[" in geo.attrib["name"] and "_LOD[0]" in geo.attrib["name"]:
            LOD0_mesh = LOD0_mesh + 1
            meshName = LOD0Name + "-" + str(LOD0_mesh)
            mesh = geo.find(DAEMesh)

            blankMesh = bpy.data.meshes.new(meshName)
            ob = bpy.data.objects.new(meshName, blankMesh)
            col = bpy.data.collections.get("Collection")
            col.objects.link(ob)

            print("Importing " + geo.attrib["name"] + " as: " + meshName)

            UVs = []

            for source in mesh.iter(DAESource):
                if "position" in source.attrib["id"].lower():
                    rawVerts = [float(i) for i in source.find(DAEFloats).text.split()]
                    print(source,"position loading...")

                if "normal" in source.attrib["id"].lower():
                    rawNormals = [float(i) for i in source.find(DAEFloats).text.split()]
                    print(source,"normal loading...")

                if "uv" in source.attrib["id"].lower():
                    rawUVs = [float(i) for i in source.find(DAEFloats).text.split()]
                    coords = [rawUVs[i:i+2] for i in range(0, len(rawUVs),2)]
                    UVs.append(coords)
                    print(source,"uv loading...")

            vertPositions = [rawVerts[i:i+3] for i in range(0, len(rawVerts),3)]
            meshNormals = [rawNormals[i:i+3] for i in range(0, len(rawNormals),3)]


            subMeshes = []

            for tris in mesh.iter(DAETris):
                # For LOD[0] visual mesh, no materials needed
                material = "None"

                maxOffset = 0
                UVOffsets = []
                vertOffset = 0
                normOffset = 0
                for inp in tris.iter(DAEInput):
                    if int(inp.attrib["offset"]) > maxOffset:
                        maxOffset = int(inp.attrib["offset"])
                    if inp.attrib["semantic"].lower() == "texcoord":
                        UVOffsets.append(int(inp.attrib["offset"]))
                    if inp.attrib["semantic"].lower() == "vertex":
                        vertOffset = int(inp.attrib["offset"])
                    if inp.attrib["semantic"].lower() == "normal":
                        normOffset =  int(inp.attrib["offset"])
                if tris.find(DAEp).text is not None:
                    splitPsoup = [int(i) for i in tris.find(DAEp).text.split()]
                    pArray = [splitPsoup[i:i+(maxOffset+1)] for i in range(0, len(splitPsoup),(maxOffset+1))]
                    # Only build the submesh if it actually has triangles
                    subMeshes.append(meshBuilder(material, vertPositions, meshNormals, UVs, vertOffset, normOffset, UVOffsets, pArray, smoothing_opt))

            #Combines the material submeshes into one mesh
            for obs in subMeshes:
                #obs.select = True # old #>
                obs.select_set(True) # seb
            #ob.select = True #>
            obs.select_set(True)
            #bpy.context.scene.objects.active = ob #>
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.join()
            ob.data.use_auto_smooth = True
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.remove_doubles()
            bpy.ops.object.editmode_toggle()
            #ob.select = False
            obs.select_set(False)
# Main

#DAEfile = "N:/001-Progetti/001-blender/001-Homeworld_Inheritance/tools/HODOR/DAE/cube dae/cube.dae"
# https://stackoverflow.com/questions/5137497/find-the-current-directory-and-files-directory
# https://medium.com/@ageitgey/python-3-quick-tip-the-easy-way-to-deal-with-file-paths-on-windows-mac-and-linux-11a072b58d5f
#data_folder = Path("N:/001-J_Lab/101-Projects/hwrm2_toolkit/files/hw_toolkit/")
#file_to_open = data_folder / "hgn_scout.dae"
file_to_open = Path("N:/001-J_Lab/101-Projects/hwrm2_toolkit/files/hw_toolkit/hgn_scout/hgn_scout.dae")
DAEfile = str(file_to_open)
if os.path.exists(DAEfile):
    print(file_to_open,"caricato!")
    ImportDAE(DAEfile,True,"","")
    #ImportLOD0(DAEfile,True)
#
# end
