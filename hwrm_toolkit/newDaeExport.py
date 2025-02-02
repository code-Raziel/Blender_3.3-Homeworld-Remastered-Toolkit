# Updated:
#  Converts all materials to phong on export
# Dom2 14-JUL-2019

import bpy,sys,os,glob
import math
import time
import shutil
from pathlib import Path
from mathutils import *
from operator import itemgetter # Sorting tool
from subprocess import Popen, PIPE
C = bpy.context
D = bpy.data



# --- Utils ---
def pause():
    programPause = input("Press the <ENTER> key to continue...")

#############
#DAE Schemas#
#############

#Just defining all the DAE attributes here so the processing functions are more easily readable

#Utility Schemas
DAENode = "{http://www.collada.org/2005/11/COLLADASchema}node"
DAETranslation = "{http://www.collada.org/2005/11/COLLADASchema}translate"
DAEInit = "{http://www.collada.org/2005/11/COLLADASchema}init_from"
DAEInput = "{http://www.collada.org/2005/11/COLLADASchema}input"
DAEFloats = "{http://www.collada.org/2005/11/COLLADASchema}float_array"
DAESource = "{http://www.collada.org/2005/11/COLLADASchema}source"
DAEInstance = "{http://www.collada.org/2005/11/COLLADASchema}instance_geometry"

##Material Schemas
DAELibMaterials = "{http://www.collada.org/2005/11/COLLADASchema}library_materials"
DAEMaterials = "{http://www.collada.org/2005/11/COLLADASchema}material"
DAELibEffects = "{http://www.collada.org/2005/11/COLLADASchema}library_effects"
DAEfx = "{http://www.collada.org/2005/11/COLLADASchema}effect"
DAELibImages = "{http://www.collada.org/2005/11/COLLADASchema}library_images"
DAEimage = "{http://www.collada.org/2005/11/COLLADASchema}image"
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


def ColorToArrayToString(color):
    colorArray = []
    # colorArray.append(color.r)
    # colorArray.append(color.g)
    # colorArray.append(color.b)
    # colorArray = str(colorArray)
    # colorArray = colorArray.translate({ord(c):None for c in '[],'})
    return colorArray

def writeTextures(dae,libImages,texName,tex_Ext):
    thisImage = dae.ET.SubElement(libImages,'image',id=texName+'-image',name=texName+'_FMT[DXT5]')
    init = dae.ET.SubElement(thisImage,'init_from')
    print("Texture = "+texName)
    #init.text = D.textures[texName].image.filepath
    init.text = texName.lstrip('IMG[').rstrip(']') + tex_Ext

def writeMaterials(dae,libMats,mat_object_list):

    for mat_object in mat_object_list:
        # Get Material Data 
        matName = mat_object.name
        thisMaterial = dae.ET.SubElement(libMats,'material',id=matName,name=matName)
        instance = dae.ET.SubElement(thisMaterial,'instance_effect',url='#'+matName+'-fx')

def writeEffects(dae,libEffects,mat_object_list):

    #Get Textures
    textures = []

    

    for mat_object in mat_object_list:
        # Get Material Data 
        matName = mat_object.name ; print('Building Shader for Material:',matName)
        matShader = ''
        if '[ship]' in matName : 
            matShader = 'ship'
        if '[thruster]' in matName:
            matShader = 'engine'
        if '[badge]' in matName:
            matShader = 'badge'
        node_tree = mat_object.node_tree
        nodes = node_tree.nodes
        bsdf = nodes.get("Principled BSDF")

        thisEffect = dae.ET.SubElement(libEffects,'effect',id=matName+'-fx',name=matName)
        profile = dae.ET.SubElement(thisEffect,'profile_COMMON')
        technique = dae.ET.SubElement(profile,'technique',sid='standard')
        #shtype = dae.ET.SubElement(technique,D.materials[matName].specular_color)
        shtype = dae.ET.SubElement(technique,'phong')  #dae.ET.SubElement(technique,D.materials[matName].specular_color)
        '''
        BSDF Map

        # 1 Subsurface
        # 2 Subsurface Radius
        # 3 Subsurface Color
        # 4 Subsurface IOR
        # 5 Subsurface Anisotropy
        # 6 Metallic
        # 7 Specular
        # 8 Specular Tint
        # 9 Roughness
        # 10 Anisotropic
        # 11 Anisotropic Rotation
        # 12 Sheen
        # 13 Sheen Tint
        # 14 Clearcoat
        # 15 Clearcoat Roughness
        # 16 IOR
        # 17 Transmission
        # 18 Transmission Roughness
        # 19 Emission
        # 20 Emission Strength
        # 21 Alpha
        # 22 Normal
        # 23 Clearcoat Normal
        # 24 Tangent
        # 25 Weight

        
        '''
        
        #                 socket, map_type  , map1_tag , map2_tag
        shader=   [
                            [ 19, 'emission','GLOW','GLOX'],
                            [ 0 , 'diffuse','DIFF','DIFX'],
                            [ 7 , 'reflective','REFL','REFX'],
                            [ 9 , 'specular','SPEC', 'SPEX'],
                            [ 22, 'normal','NORM', None],
                            [ 3 , 'race'  , 'STRP', 'TEAM']

                        ] 
     
        
        tex_nodes = []
        for map in shader:
            
            # Clear loop data
            img_texture = None
            tex_nodes = []
            #Map Data
            map_input = map[0]
            map_name = map[1] 
            map_type = map[2]
            map_sec = map[3]
            
            
            if len(bsdf.inputs[map_input].links)>0 :
                print(bsdf.inputs[map_input].name) # emission_socket
                print('Links:',bsdf.inputs[map_input].links[0])
                # Get emission node : direct
                input_node = bsdf.inputs[map_input].links[0].from_node
                print ('BSDF input node:',input_node.type)
                #print("267:",emission_node.name); pause()
                
                if input_node.type is not None :
                    
                    if 'TEX_IMAGE' in input_node.type:
                        tex_nodes.append(input_node)
                    
                    elif 'MIX' in input_node.type:

                        tex_nodes.append(input_node.inputs[6].links[0].from_node)
                        tex_nodes.append(input_node.inputs[7].links[0].from_node)

                    elif 'NORMAL_MAP' in input_node.type:
                        tex_nodes.append( input_node.inputs[1].links[0].from_node ) # NORMAL_MAP from input_Color node
                        
                    for tex_node in tex_nodes:
                        print(tex_node.label)
                        if tex_node.image:
                            img_name =  tex_node.image.name[:-4]
                            _ext = tex_node.image.name[-4:]
                            map_type = tex_node.label[:4]
                            
                            textures.append([img_name,_ext,matShader,map_type])

                            if map_type in ['DIFF','GLOW','SPEC','REFL','NORM'] :
                                
                                img_texture = 'IMG[' + dae.ship_name + '_' + matShader + '_' + map_type  + ']'
                                # Write ETree
                                shader_map = dae.ET.SubElement(shtype,map_name)    
                                e_texture = dae.ET.SubElement(shader_map,'texture',texture=img_texture+'-image') # |DEPR| texcoord='CHANNEL0'
                                e_extra = dae.ET.SubElement(e_texture,'extra')
                                e_extra_technique = dae.ET.SubElement(e_extra,'technique',profile='MAYA')
                                wrapU = dae.ET.SubElement(e_extra_technique,'wrapU',sid='wrapU0')
                                wrapU.text='TRUE'
                                wrapV = dae.ET.SubElement(e_extra_technique,'wrapV',sid='wrapV0')
                                wrapV.text='TRUE'
                                blend = dae.ET.SubElement(e_extra_technique,'blend_mode')
                                #blend.text is for video sequencer
                                #https://b3d.interplanety.org/en/adding-video-strip-to-the-vse-sequencer-with-blender-python-api/
                                blend.text = 'ADD' # set to static add
                        else: 
                            print('Empty Image Node')
                        
                    
                    
                    
                    
                    
                    
            
        #Ambient
        ambient = dae.ET.SubElement(shtype,'ambient')
        color = dae.ET.SubElement(ambient,'color',sid='ambient')
        W_Color = ' '.join([ str(c) for c in D.worlds['World'].color[0:3]])
        W_Strength = str(D.worlds['World'].node_tree.nodes["Background"].inputs[1].default_value)
        color.text = W_Color + ' ' + W_Strength

        # Shininess Mapped on the BSDF Roughness
        shininess = dae.ET.SubElement(shtype,'shininess')
        shine = dae.ET.SubElement(shininess,'float',sid='shininess')
        specular_hardness = str(bsdf.inputs[9].default_value)
        shine.text = specular_hardness
        
        # Reflective Node extraction
        Subsurface_Strength = str(bsdf.inputs[9].default_value)
        rev_subcolor = [ str(1-c) for c in bsdf.inputs[3].default_value[0:3]]
        rev_subcolor.append( str(bsdf.inputs[3].default_value[3]) )
        Subsurface_Color = ' '.join( rev_subcolor )
        mirror_color = Subsurface_Color
        
        # Reflective Mapped on the BSDF Subsurface Color
        reflective = dae.ET.SubElement(shtype,'reflective')
        color = dae.ET.SubElement(reflective,'color',sid='reflective')
        color.text = mirror_color
        

        # Reflectivity Mapped on the BSDF Subsurface
        reflectivity = dae.ET.SubElement(shtype,'reflectivity')
        float = dae.ET.SubElement(reflectivity,'float',sid='reflectivity')
        float.text = str(1-bsdf.inputs[1].default_value)
    
        #Transparent Mapped on the BSDF ???
        transparent = dae.ET.SubElement(shtype,'transparent',opaque="RGB_ZERO")
        color = dae.ET.SubElement(transparent,'color',sid='transparent')
        color.text = '1.000000 1.000000 1.000000 1.000000'

        #Transparency Mapped on the BSDF Alpha (reversed)
        transparency = dae.ET.SubElement(shtype,'transparency')
        float = dae.ET.SubElement(transparency,'float',sid='transparency')
        alpha = bsdf.inputs[21].default_value
        alpha_reversed = ( 1 - alpha )
        float.text = str( alpha_reversed )

    return textures
 
def writeGeometry(dae,libgeo,geoName):
    #Triangulate the Mesh
    thisGeo = dae.ET.SubElement(libgeo,'geometry',id=(geoName+'-lib'),name = (geoName+'Mesh'))
    thisMesh = dae.ET.SubElement(thisGeo,'mesh')
    C.view_layer.objects.active = D.objects[geoName]
    
    #C.scene.objects.active = D.objects[geoName] # old
    #C.scene.objects.active(D.objects[geoName]) 
    bpy.ops.object.modifier_add(type='TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier='Triangulate')
    
    mesh = D.objects[geoName].data
    mesh.calc_loop_triangles() # suspended
    print("Geo Mesh:",mesh.name)
    mesh.use_auto_smooth = True
    mesh.calc_normals_split() # suspended
    
    #Create the Vertices
    vertices = []
    """ vertices_index is normals_index[0] """

    for v in mesh.vertices:
        vertices.append( round(v.co.x,6) )
        vertices.append( round(v.co.y,6) )
        vertices.append( round(v.co.z,6) )

    meshPositions = dae.ET.SubElement(thisMesh,'source',id=geoName+'-POSITION')
    vertArray = dae.ET.SubElement(meshPositions,'float_array',id=meshPositions.attrib['id']+'-array',count=str(len(vertices)))
    
    vertices = str(vertices)
    vertArray.text = ' ' + vertices.translate({ord(c):None for c in '[],\''}) # Delete '[],' characters in the string 
    technique = dae.ET.SubElement(meshPositions,'technique_common')
    accessor = dae.ET.SubElement(technique,'accessor',source='#'+vertArray.attrib['id'],count=str(len(mesh.vertices)),stride='3')
    paramX = dae.ET.SubElement(accessor,'param',name='X',type='float')
    paramY = dae.ET.SubElement(accessor,'param',name='Y',type='float')
    paramZ = dae.ET.SubElement(accessor,'param',name='Z',type='float')
    
    #Create the Normals
    normals = []
    normals_index = []

    # # print('Normals length:',len(mesh.loops))
    for v in mesh.loops:
        normals.append([ round(v.normal.x,4), round(v.normal.y,4), round(v.normal.z,4)])
        #print("Vertex index :",v.vertex_index)
        normals_index.append( [ v.vertex_index, [ round(v.normal.x,4), round(v.normal.y,4), round(v.normal.z,4) ] ])
    print('Normals:',len(normals),'\n')
    #[ print(normal) for normal in normals ];pause()
    #[ print(normal) for normal in normals_index ];pause()
    
    
    normals_positions = []
    [ normals_positions.append(normal) for normal in normals if normal not in normals_positions];
    print('Normals Positions:',len(normals_positions),'\n')
    #[ print(normal) for normal in normals_positions ];pause()

    for i in normals_index:
        for pos in normals_positions:
            if i[1] == pos:
                i[1] = normals_positions.index(pos)

    #Create the Normals
    meshNormals = dae.ET.SubElement(thisMesh,'source',id=geoName+'-Normal0')
    normalArray = dae.ET.SubElement(meshNormals,'float_array',id=meshNormals.attrib['id']+'-array',count = str(len(normals_positions*3)))
    normals = str( normals_positions )
    normalArray.text = normals.translate({ord(c):None for c in '[],\''})
    technique = dae.ET.SubElement(meshNormals,'technique_common')
    accessor = dae.ET.SubElement(technique,'accessor',source='#'+normalArray.attrib['id'],count=str(int(len(normals_positions))),stride='3')
    paramX = dae.ET.SubElement(accessor,'param',name='X',type='float')
    paramY = dae.ET.SubElement(accessor,'param',name='Y',type='float')
    paramZ = dae.ET.SubElement(accessor,'param',name='Z',type='float') 
            
    # (Just UVmap0 )
    if mesh.uv_layers and 'COL' not in mesh.name : 
        mesh.uv_layers.active.data  # Get uv_layer active object data
        uv_layer = mesh.uv_layers[0]
        print('mesh_data.uv_layers.data (active):', uv_layer)
        print('layer UVmap :', uv_layer.name)
        UVmap = uv_layer.name


        UVs = []
        uv_index = []
        iv = 0 ; # per vertex loop index
        for poly in mesh.polygons: # poly = []

            for loop_index in range(poly.loop_start, (poly.loop_start + poly.loop_total) ):
                vertex_index = mesh.loops[loop_index].vertex_index
                UVs.append( [ round(uv_layer.data[loop_index].uv.x,4), round(uv_layer.data[loop_index].uv.y,4) ] )
                uv_index.append( [ vertex_index, [round(uv_layer.data[loop_index].uv.x,4), round(uv_layer.data[loop_index].uv.y,4)]  ] )
                    
        uv_positions = []
        [ uv_positions.append(uv) for uv in UVs if uv not in uv_positions]; # Delete duplicated uvs
        print('UVs Positions:',len(uv_positions),'\n')
        #[ print(uv) for uv in uv_positions ];pause()

        for i in uv_index:
            for pos in uv_positions:
                if i[1] == pos:
                    i[1] = uv_positions.index(pos)

        # Visual studio Code Splitting p soup
        # Find (\d{1,3}\s\d{1,3}\s\d{1,3})\s
        # Replace $1\n

        # Create UVs
        #thisMap = dae.ET.SubElement(thisMesh,'source',id=(geoName+uvi.name))
        thisMap = dae.ET.SubElement(thisMesh,'source',id=(geoName+"-UV0"))
        array = dae.ET.SubElement(thisMap,'float_array',id=thisMap.attrib['id']+'-array',count = str(len(uv_positions)*2))
        coords = str(uv_positions)
        array.text = coords.translate({ord(c):None for c in '[],'})
        technique = dae.ET.SubElement(thisMap,'technique_common')
        accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = str(len(uv_positions)),stride='2')
        #accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = '0',stride='2')
        paramS = dae.ET.SubElement(accessor,'param',name='S',type='float')
        paramT = dae.ET.SubElement(accessor,'param',name='T',type='float')
    
    #Tell it where the vertices are
    vertElement = dae.ET.SubElement(thisMesh,'vertices',id=geoName+'-VERTEX')
    input = dae.ET.SubElement(vertElement,'input',semantic='POSITION',source=( '#'+meshPositions.attrib['id'] ))
    
    # #Make the Triangles
    if len(mesh.materials)>0 and mesh.materials[0] is not None :
        mat_start = 0
        for m in range(0,len(mesh.materials)):
            
            print("+++"+str(m)+", len(mesh.materials)="+str(len(mesh.materials)),mesh.materials[m])
            mat = mesh.materials[m]
            #print(mat)
            polys = []
            for p in mesh.polygons:
                if p.material_index == m:
                    polys.append(p)
            mat_length = len(polys)*3
            print('Material length:',mat.name,len(polys)*3)

            tris = dae.ET.SubElement(thisMesh,'triangles',count=str(len(polys)),material = mat.name)
            inputVert = dae.ET.SubElement(tris,'input',semantic='VERTEX',offset='0',source='#'+vertElement.attrib['id'])
            inputNormal = dae.ET.SubElement(tris,'input',semantic='NORMAL',offset ='1',source = '#'+ meshNormals.attrib['id'])
            map = dae.ET.SubElement(tris,'input',semantic = 'TEXCOORD',offset='2',set='0',source='#'+thisMap.attrib['id'] )
            pElement = dae.ET.SubElement(tris,'p')
            # --- p Soup mixer
            p_data = []
            for i in range( mat_start , (mat_start+mat_length) ):
                p_data.append(normals_index[i][0])
                p_data.append(normals_index[i][1]) 
                p_data.append(uv_index[i][1])
            # pElement.text = p_data.translate({ord(c):None for c in '[],'})
            pElement.text = ' ' + str(p_data).translate({ord(c):None for c in '[],'})
            mat_start = mat_start + mat_length
    else:
        polys = []
        for p in mesh.polygons:
            polys.append(p)
        tris = dae.ET.SubElement(thisMesh,'triangles',count=str(len(polys)))
        inputVert = dae.ET.SubElement(tris,'input',semantic='VERTEX',offset='0',source='#'+vertElement.attrib['id'])
        inputNormal = dae.ET.SubElement(tris,'input',semantic='NORMAL',offset ='1',source = '#'+ meshNormals.attrib['id'])        
        pElement = dae.ET.SubElement(tris,'p')
        pVerts = []
        pInds = []
        for p in mesh.polygons:
            for i in p.vertices:
                pVerts.append(i)
        for p in polys:
            for i in p.loop_indices:
                pInds.append(pVerts[i])
                pInds.append(i)
        pInds = str(pInds)
        pElement.text = ' ' + pInds.translate({ord(c):None for c in '[],'})
        
        
def writeAnims(dae,libanims,objName):
    
    thisAnim = dae.ET.SubElement(libanims,'animation',id=objName+'-anim',name=objName)
    
    if D.objects[objName].animation_data.action is not None:
        for curve in D.objects[objName].animation_data.action.fcurves:
            thisCurve = dae.ET.SubElement(libanims,'animation')
            print(curve.data_path+" "+str(curve.array_index))
            
            baseID = None
            
            if curve.data_path == 'location':
                baseID = objName+'-translate'
                if curve.array_index == 0:
                    baseID = baseID+'.X'
                if curve.array_index == 1:
                    baseID = baseID+'.Y'
                if curve.array_index == 2:
                    baseID = baseID+'.Z'
                    
            if curve.data_path == 'rotation_euler':
                baseID = objName+'-rotate'
                if curve.array_index == 0:
                    baseID = baseID+'X.ANGLE'
                if curve.array_index == 1:
                    baseID = baseID+'Y.ANGLE'
                if curve.array_index == 2:
                    baseID = baseID+'Z.ANGLE'
            
            if curve.data_path == 'scale':
                baseID = objName+'-scale'
                if curve.array_index == 0:
                    baseID = baseID+'.X'
                if curve.array_index == 1:
                    baseID = baseID+'.Y'
                if curve.array_index == 2:
                    baseID = baseID+'.Z'
            
            keys = []
            values = []
            interp = []
            intan = []
            outtan = []
            
            for k in curve.keyframe_points:
                keys.append(k.co.x/C.scene.render.fps)
                #if curve.data_path == 'location':
                if curve.data_path == 'location' or curve.data_path == 'scale':
                    values.append(k.co.y)
                if curve.data_path == 'rotation_euler':
                    values.append(math.degrees(k.co.y))
                interp.append(k.interpolation)
                intan.append(k.handle_left.x)
                intan.append(k.handle_left.y)
                outtan.append(k.handle_right.x)
                outtan.append(k.handle_right.y)
            
            #Sampler
            sampler = dae.ET.SubElement(thisCurve,'sampler',id=baseID)
            
            #Create the input values (keyframes)
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-input')
            input = dae.ET.SubElement(sampler,'input',semantic = 'INPUT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-input-array',count = str(len(keys)))
            array.text = str(keys).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride = '1')
            param = dae.ET.SubElement(accessor,'param',type='float')
            
            #Create the output values (actual values)
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-output')
            input = dae.ET.SubElement(sampler,'input',semantic = 'OUTPUT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-output-array',count = str(len(values)))
            array.text = str(values).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride = '1')
            param = dae.ET.SubElement(accessor,'param',type='float')
            
            #Create the interpolations
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-interpolation')
            input = dae.ET.SubElement(sampler,'input',semantic='INTERPOLATION',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'Name_array',id=baseID+'-interpolation-array',count = str(len(interp)))
            array.text = str(interp).translate({ord(c):None for c in '[],\''})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = array.attrib['count'],stride='1')
            param = dae.ET.SubElement(accessor,'param',type='name')
            
            #Intangents for Bezier Curves
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-intan')
            input = dae.ET.SubElement(sampler,'input',semantic='IN_TANGENT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-intan-array',count = str(len(intan)))
            array.text = str(intan).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source = '#'+array.attrib['id'],count = str(len(intan)/2),stride = '2')
            paramA = dae.ET.SubElement(accessor,'param',type='float')
            paramB = dae.ET.SubElement(accessor,'param',type='float')
            
            #Outtangents for Bezier Curves
            source = dae.ET.SubElement(thisCurve,'source',id=baseID+'-outtan')
            input = dae.ET.SubElement(sampler,'input',semantic='OUT_TANGENT',source='#'+source.attrib['id'])
            array = dae.ET.SubElement(source,'float_array',id=baseID+'-outtan-array',count = str(len(outtan)))
            array.text = str(outtan).translate({ord(c):None for c in '[],'})
            technique = dae.ET.SubElement(source,'technique_common')
            accessor = dae.ET.SubElement(technique,'accessor',source='#'+array.attrib['id'],count = str(len(outtan)/2),stride = '2')
            paramA = dae.ET.SubElement(accessor,'param',type='float')
            paramB = dae.ET.SubElement(accessor,'param',type='float')
            
            channel = dae.ET.SubElement(thisCurve,'channel',source='#'+baseID,target=baseID.split('-')[0]+'/'+baseID.split('-')[1])
        
        
def writeNodes(dae,parentNode,libgeo,libanims,objectName):
    print("Writing Node for "+objectName)
    thisNode = dae.ET.SubElement(parentNode,'node',name=objectName,id=objectName,sid=objectName)
    thisPosition = dae.ET.SubElement(thisNode,'translate',sid='translate')
    thisPosition.text = str(D.objects[objectName].matrix_local.translation.x)+' '+str(D.objects[objectName].matrix_local.translation.y)+' '+str(D.objects[objectName].matrix_local.translation.z)
    rotZ = dae.ET.SubElement(thisNode,'rotate',sid='rotateZ')
    rotZ.text = '0 0 1 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().z))
    rotY = dae.ET.SubElement(thisNode,'rotate',sid='rotateY')
    rotY.text = '0 1 0 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().y))
    rotX = dae.ET.SubElement(thisNode,'rotate',sid='rotateX')
    rotX.text = '1 0 0 '+str(math.degrees(D.objects[objectName].matrix_local.to_euler().x))
    if D.objects[objectName].animation_data is not None:
        writeAnims(dae,libanims,objectName)

    if D.objects[objectName].type == 'MESH':
        geoInstance = dae.ET.SubElement(thisNode,'instance_geometry',url='#'+objectName+'-lib')
        bindMat = dae.ET.SubElement(geoInstance,'bind_material')
        matTechnique = dae.ET.SubElement(bindMat,'technique_common')
        for m in D.objects[objectName].material_slots:
            matInstance = dae.ET.SubElement(matTechnique,'instance_material',symbol = m.name,target='#'+m.name)            
        writeGeometry(dae,libgeo,objectName)
    #Get Navlight Data and change append it into Node name
    if D.objects[objectName].type == 'LAMP':    
        print('Found Lamp '+objectName)
        lamp = D.objects[objectName].data
        if hasattr(lamp,'["Phase"]'): # Need to pick up on "Phase" to avoid confusion with BackgroundLights -- Dom2
            print('Found NavLight')
            lampColorR = str(lamp.color.r)
            lampColorG = str(lamp.color.g)
            lampColorB = str(lamp.color.b)
            lampSize = str(lamp.energy)
            lampDist = str(lamp.distance)
            lampPhase = str(lamp["Phase"])
            lampFreq = str(lamp["Freq"])
            lampType = lamp["Type"]
            
            newName = objectName+'_Type['+lampType+']_Sz['+lampSize+']_Ph['+lampPhase+']_Fr['+lampFreq+']_Col['+lampColorR+','+lampColorG+','+lampColorB+']_Dist['+lampDist+']'
            
            if hasattr(lamp,'["Flags"]'):
                lampFlags = lamp["Flags"]
                newName = newName+'_Flags['+lampFlags+']'
            
            print(newName)
            thisNode.set('id',newName)
            thisNode.set('name',newName)   
            thisNode.set('sid',newName)
            
        elif hasattr(lamp,'["Atten"]'): # Need to pick up on "Atten" to avoid confusion with NavLights -- Dom2
            print('Found BackgroundLight')
            lampColorR = str(lamp.color.r)
            lampColorG = str(lamp.color.g)
            lampColorB = str(lamp.color.b)
            # Not sure how to grab the spec yet...
            #lampSpecR = str(lamp.specular.r)
            #lampSpecG = str(lamp.specular.g)
            #lampSpecB = str(lamp.specular.b)
            lampAtten = lamp["Atten"]
            lampType = lamp["Type"]
            
            newName = objectName+'_Type['+lampType+']_Diff['+lampColorR+','+lampColorG+','+lampColorB+']_Spec[0,0,0]_Atten['+lampAtten+']'
            
            print(newName)
            thisNode.set('id',newName)
            thisNode.set('name',newName)   
            thisNode.set('sid',newName)
            
    #Parse Dock Node Data and append to name
    if 'DOCK[' in objectName:
        print("Found Dock path "+objectName)
        dockNode = D.objects[objectName]
        if hasattr(dockNode,'["Fam"]'):
            shipFam = dockNode['Fam']
            newName = objectName+'_Fam['+shipFam+']'
            if hasattr(dockNode,'["Link"]'):
                dockLink = dockNode["Link"]
                newName = newName+'_Link['+dockLink+']'
            if hasattr(dockNode,'["Flags"]'):
                dockFlags = dockNode["Flags"]
                newName = newName+'_Flags['+dockFlags+']'
            if hasattr(dockNode,'["MAD"]'):
                dockMAD = str(dockNode["MAD"])
                newName = newName+'_MAD['+dockMAD+']'
            
            thisNode.set('id',newName)
            thisNode.set('name',newName)
            thisNode.set('sid',newName)
     
    #Parse Seg Nodes
    if 'SEG[' in objectName:
        segNode = D.objects[objectName]
        if hasattr(segNode,'["Speed"]'):
            newName = objectName.split('.')[0]
            segTol = str(int(segNode.empty_draw_size))
            segSpeed = str(segNode["Speed"])
            newName = newName+'_Tol['+segTol+']_Spd['+segSpeed+']'
            if hasattr(segNode,'["Flags"]'):
                segFlags = segNode["Flags"]
                newName = newName+'_Flags['+segFlags+']'
            
            thisNode.set('id',newName)
            thisNode.set('name',newName)
            thisNode.set('sid',newName)
    
    #Parse MAT[xxx]_PARAM[yyy] Nodes
    if 'MAT[' in objectName and 'PARAM[' in objectName:
        print("This is a MAT[xxx]_PARAM[yyy] joint...")
        matPexNode = D.objects[objectName]
        newName = objectName.split('.')[0] # in case it is "MAT[xxx]_PARAM[yyy]_Type[RGBA].001"
        print(str(newName))
        """
        if hasattr(matPexNode,'["Type6"]'):
            matPEXtype = str(matPexNode["Type6"])
            newName = newName+'_Type6['+matPEXtype+']'
        if hasattr(matPexNode,'["Type"]'):
            matPEXtype = str(matPexNode["Type"])
            newName = newName+'_Type['+matPEXtype+']'
        """
        # If the joint has custom properties, build them into the name
        if len(matPexNode.keys())>1:
            newName = newName + "_Data["
            for p in matPexNode.keys():
                print("found parameter " + str(p))
                if p.startswith("data"):
                    print("it is a data paramter")
                    if newName.endswith("["):
                        newName = newName + str(matPexNode[p])
                    else:
                        newName = newName + "," + str(matPexNode[p])
            newName = newName + "]" # Joint name should now be "MAT[xxx]_PARAM[yyy]_Type[RGBA]_Data[i,k,j]"

        thisNode.set('id',newName)
        thisNode.set('name',newName)
        thisNode.set('sid',newName)
    
    if D.objects[objectName].children is not None:
        for c in D.objects[objectName].children:
            writeNodes(dae,thisNode,libgeo,libanims,c.name)


def prettify(root):
    indentation_list = [[0,'?xml version=\'1.0\' encoding=\'utf-8\'?>']]
    def monsterify(tree_element, parent, level):
        indent = '    '
        level = level;
        if len(tree_element.findall('./'))>0: # if parent it got childs so indent childs one more level
            num_childs = len(tree_element.findall('./'))
            #print(level,tree_element.tag, num_childs)
            indentation_list.append([level,tree_element.tag])
            tree_element.text = '\n'
            tree_element.tail = '\n'
            #parent.indent(tree_element,space='    ',level=level)
            #print(parent.tag,"has childrens")
            for child in tree_element.findall('./'):
                monsterify( tree_element = child, parent=tree_element, level = (level+1) )
        else:
            #print(level,tree_element.tag,"No Childs")
            indentation_list.append([level,tree_element.tag])
            tree_element.tail = '\n'
    monsterify( tree_element = root, parent = root, level = 0 )
    return indentation_list

def reindent(filepath,indentation_list):
    # Due to tree_element.text and  tree_element.tail inconsistency , file must be reindented (2nd step)
    #[print(i) for i in indentation_list]
    space = '    '
    newfile = []
    i=0
    ln=0
    i_search=0
    with open(filepath, 'r') as file:
        
        for line in file:
            line = line.rstrip('\n')
            #print('i',i)
            #print(indentation_list[i][1])
            #print(i,ln)  
            if  line.startswith('<' + indentation_list[i][1] + ' /') or \
                line.startswith('<' + indentation_list[i][1]) :
                
                level = indentation_list[i][0]
                newfile.append(space * level + line)
                #print(space * level + line)
                if i < (len(indentation_list)-1):
                    i=i+1
            else :
                #print('Last element',i,indentation_list[i][1])
                i_search = i-1
                while not line.startswith('</'+ indentation_list[i_search][1]):
                    i_search= i_search-1
                level = indentation_list[i_search][0]
                newfile.append(space * level + line)
                indentation_list[i_search][1] = '-'
                # #print(space * level + line)
                # i = curr_i
            ln+=1
    del file
    with open(filepath, 'w') as file:
        for line in newfile:
            file.write(line + '\n')
    del file

def hod_make(filepath,ship_name,hwrm_dir):
    hodor = str(Path(__file__).resolve().parent / 'HODOR' / 'make_HOD.bat')
    #hwrm_dir = hwrm_dir.replace(' ','\')
    print('Homeworld directory:',hwrm_dir)
    # hodor = str(Path(__file__).resolve().parent / 'HODOR' / 'HODOR.exe')
    #os.popen(f'START CMD /K "{hodor}" {collection.name}')
    Popen(f'''START CMD /C ""{hodor}" {ship_name} "{hwrm_dir}"" ''',shell=True )
    

def ExportImages(exp_dir,ship_name,textures):
    # Deleting old .tga texture files
    pattern = str(exp_dir)+ '\\' + "*.tga"
    #print('Cleaning Pattern:',pattern)
    texs = glob.glob(pattern)
    for tex in texs:
        #print('Cleaning file:',tex)
        os.remove(tex)

    # Saving files to ship directory
    for image in bpy.data.images:
        for tex in textures:
            if image.name[:-4] in tex:
                if image.packed_file is not None:
                    print('Exporting packed texture image:',image.name)
                    image.filepath = str( exp_dir / ( ship_name+'_'+tex[2]+'_'+tex[3]+tex[1] ) )
                    image.save()
                else : 
                    print('Exporting external Texture Image :',image.name )
                    src = str(bpy.path.abspath(image.filepath))
                    #print("Source file :",src)
                    dst = str( exp_dir / ( ship_name+'_'+tex[2]+'_'+tex[3]+tex[1] ) )
                    print("Destination file :",dst)
                    shutil.copyfile(src, dst)
                    #image.save_render(filepath = str( exp_dir / image.name ) )
        #bpy.data.textures[name].image = bpy.data.images.load(image_path)

def ExportScripts(exp_dir):
    for text in bpy.data.texts:
        #if text.is_in_memory:
        #    continue
        path = Path(bpy.path.abspath(text.filepath))
        if 'events' in text.name:
            path = exp_dir / text.name.replace('_events.txt','.events' )
        path.write_text(text.as_string())
        print("Exporting Script : ", path )
        #print('Exporting scripts:',text.name)
        #if 'events' in text.name:
        #    pass
        #text.filepath = str( exp_dir / text.name )
        #text.save()
    #bpy.data.textures[name].image = bpy.data.images.load(image_path)

def get_hwrm_dir():
    key= r'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 244160'
    output = Popen(f'CMD /C Reg Query "{key}" /v InstallLocation',universal_newlines=True,stdout=PIPE,shell=True, text=True )
    output = output.stdout.read()
    if "InstallLocation" in output:
        output = output[(88+34):]
        return output
    else:
        output = 'Not Found'
        return output

class HwDAE:
    import xml.etree.ElementTree as ET
    ship_name = ""
    
    #--- Main
    def doExport(self,filepath,hwrm_dir,make_hod):
        
        #Set up Collada Header Stuff
        print('Writing Root: assets')
        root = self.ET.Element('COLLADA',version='1.4.1',xmlns = 'http://www.collada.org/2005/11/COLLADASchema')
        asset = self.ET.SubElement(root,'asset')
        contributorTag = self.ET.SubElement(asset,'contributor')
        contribAuthor = self.ET.SubElement(contributorTag,'author')
        contribAuthor.text = 'Homeworld Inheritance and Anonymous'
        contribTool = self.ET.SubElement(contributorTag,'authoring_tool')
        contribTool.text = 'New Collada Exporter for Blender, by David Lejeune , updated by Sebastiano Paganin '
        createdDate = self.ET.SubElement(asset,'created')
        createdDate.text = time.ctime()
        modifiedDate = self.ET.SubElement(asset,'modified')
        modifiedDate.text = time.ctime()
        units = self.ET.SubElement(asset,'unit',meter='1.0',name='meter')
        upAxis = self.ET.SubElement(asset,'up_axis')
        upAxis.text = 'Z_UP'

        print('Writing Library Images')
        libImages = self.ET.SubElement(root,'library_images')

        print('Writing Library Materials')
        libMats = self.ET.SubElement(root,'library_materials')
        writeMaterials(self,libMats,self.get_mat_list())

        print('Writing Library Effects')
        libEffects = self.ET.SubElement(root,'library_effects')
        textures = writeEffects(self,libEffects,self.get_mat_list())

        print('Writing Library Geometries')
        libGeometries = self.ET.SubElement(root,'library_geometries')

        print('Writing Library Animations')
        libAnimations = self.ET.SubElement(root,'library_animations')

        #Write the Library Visual Scenes Stuff
        print('Writing Library Visual Scenes')
        libScenes = self.ET.SubElement(root,'library_visual_scenes')    
        thisScene = self.ET.SubElement(libScenes,'visual_scene',id=self.ship_name,name=self.ship_name)
        daeScene = self.ET.SubElement(root,'scene')
        visScene = self.ET.SubElement(daeScene,'instance_visual_scene',url='#'+thisScene.attrib["id"])
    
        
        for ob in D.objects:
            if ob.parent is None:
                writeNodes(self,thisScene,libGeometries,libAnimations,ob.name)

        for tex in textures:
            print('texture',tex[0]+tex[1])
            #if hasattr(tex,'image'):
            writeTextures(self,libImages,('IMG['+self.ship_name+'_'+tex[2]+'_'+tex[3]+']'),tex[1])
        
        
        
        pretty = prettify(root)
        #[print(i) for i in indentation_list]
        doc = self.ET.ElementTree(root)
        #doc.write('F:\\mymod\\Test.dae',encoding = 'utf-8',xml_declaration=True)

        print(filepath)
        #exp_dir = str( Path(filepath).resolve().parent / collection.name )
        # get_hwrm_dir() 
        exp_dir = Path(filepath).resolve().parent   
        doc.write(filepath,encoding='utf-8',xml_declaration=True)
        reindent(filepath,pretty)
        ExportImages(exp_dir,self.ship_name,textures)
        ExportScripts(exp_dir)
        if make_hod:
            hod_make(filepath,self.ship_name,hwrm_dir)
        

    def get_mat_list(self):

        Sorted_materials = ['ship','thruster','badge'] ; mat_sorted = [] ;
        for word in Sorted_materials:
            for mat in D.materials:
                print(mat.name)
                if word in mat.name : 
                    mat_sorted.append(mat)

        # if other_materials is not None : 
        #     Sorted_materials.extend(other_materials)
        return mat_sorted

    def __init__(self):
        self.data = []
        self.ship_name = bpy.data.collections[0].name
        
    
def save(filepath,hwrm_dir,make_hod): 
    bpy.ops.wm.console_toggle()
    thisDAE = HwDAE()
    thisDAE.doExport(filepath,hwrm_dir,make_hod)
    print('\nProcess Complete. END ')
    bpy.ops.wm.console_toggle()
    return{'FINISHED'}
    



### Main Tester
#print(sys.argv[1])
#filepath = sys.argv[1]

#save(filepath)