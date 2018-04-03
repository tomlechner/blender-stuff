#
# This file is released under the GPL V2 or later (same as Blender).
#
# Copyright Tom Lechner (tomlechner.com) 2018
#
#



import bpy
from math import radians


#
# TODO
# ----
# extra update panel? change base settings like caps after creation, otherwise all the drivers break
# resolve the dependency cycle blender thinks it finds (doesn't actually break anything)
#


bl_info = {
    "name":        "Building Arrayer",
    "description": "Create a building from wall and corner blocks with arrays and drivers",
    "author":      "Tom Lechner",
    "version":     (0, 1, 0),
    "blender":     (2, 7, 8),
    "location":    "View 3D > Tool Shelf",
    "warning":     "",  # used for warning icon and text in addons panel
    #"wiki_url":    "http://tomlechner.com/blender",
    #"tracker_url": "https://github.com/CGCookie/retopoflow/issues",
    "category":    "3D View"
    }


class BuildOutPanel(bpy.types.Panel):
    """Create building from a wall object"""
    bl_label = "Build Arrayer"
    bl_idname = "SCENE_PT_layout"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    bl_context = "objectmode"

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        # Create a simple row.
        layout.label(text="Building arrays:")
        row = layout.row(align = True)
        row.prop(scene, "buo_width")
        row.prop(scene, "buo_depth")
        row.prop(scene, "buo_height")


        #Wall object
        #layout.label(text="Wall object:")
        layout.prop_search(scene, "buo_WallObject", scene, "objects")
        layout.prop_search(scene, "buo_WallTop",    scene, "objects")
        layout.prop_search(scene, "buo_WallBottom", scene, "objects")

        layout.prop_search(scene, "buo_Corner",      scene, "objects")
        layout.prop_search(scene, "buo_CornerTop",   scene, "objects")
        layout.prop_search(scene, "buo_CornerBottom",scene, "objects")

        layout.prop(scene, "buo_Floors")
        layout.prop_search(scene, "buo_FloorMaterial", bpy.data, "materials")
        layout.prop_search(scene, "buo_RoofMaterial",  bpy.data, "materials")
        layout.prop(scene, "buo_DestructoBall")
        
        #Create
        layout.label(text="")
        row = layout.row()
        #row.scale_y = 2.0
        row.operator("buo_create.create")


def BUO_WallMeshObject_poll(self, object):
    """ only work on mesh objects """
    return object.type == 'MESH'


class BUO_CreateWallOperator(bpy.types.Operator):
    bl_idname = "buo_create.create"
    bl_label = "Create"
    bl_description = "Construct a building with this wall piece. +x is out facing."
    bl_options = { 'REGISTER', 'UNDO' }
 
    def addTallDriver(self, top, obj, plusone=False):
        self.addCountDriver(top,obj, "Tall", '["buo_tall"]', plusone)
        
    def addCountDriver(self, top, obj, which, path, plusone = False):
        fcurve = obj.driver_add('modifiers["'+which+'"].count')
        if plusone:
            fcurve.driver.expression = "count+1"
        else:
            fcurve.driver.expression = "count"
        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = path

    def addBoneDriver(self, top, armature, which, wallobj, size):
        prop = ""
        path = ""
        expression = ""
        if which==0:
            prop = '["buo_wide"]'
            expression = "int(abs(p/v)*2)"
            path = 'pose.bones["DimsWidget"].location[0]'
        elif which == 1:
            prop = '["buo_deep"]'
            expression = "int(abs(p/v)*2)"
            path = 'pose.bones["DimsWidget"].location[2]'
        else:
            prop = '["buo_tall"]'
            expression = "int(abs(p/v)-1)"
            path = 'pose.bones["DimsWidget"].location[1]'
            
        fcurve = top.driver_add(prop)
        fcurve.driver.expression = expression
        
        dvar = fcurve.driver.variables.new()
        dvar.name='p'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = armature
        target.data_path = path

        dvar = fcurve.driver.variables.new()
        dvar.name='v'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobj
        target.data_path = size

    def addRoofZDriver(self, top, roof, wallobject, walltop, wallbottom):
        fcurve = roof.driver_add('location', 2)
        fcurve.driver.expression = "count * wallz - roofthickness"

        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = '["buo_tall"]'

        dvar = fcurve.driver.variables.new()
        dvar.name='wallz'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'dimensions[2]'

        dvar = fcurve.driver.variables.new()
        dvar.name='roofthickness'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = roof
        target.data_path = 'dimensions[2]'
        
        if walltop!= None:
            fcurve.driver.expression = fcurve.driver.expression + " + toph"
            dvar = fcurve.driver.variables.new()
            dvar.name='toph'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = walltop
            target.data_path = 'dimensions[2]'

        if wallbottom!= None:
            fcurve.driver.expression = fcurve.driver.expression + " + bottomh"
            dvar = fcurve.driver.variables.new()
            dvar.name='bottomh'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = wallbottom
            target.data_path = 'dimensions[2]'


    def addXDriver(self, top, obj, wallobject, path, expression, cornerobject):
        fcurve = obj.driver_add('location', 0)
        fcurve.driver.expression = expression

        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = path

        dvar = fcurve.driver.variables.new()
        dvar.name='piecewidth'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'dimensions[1]'
        
        if cornerobject != None:
            dvar = fcurve.driver.variables.new()
            dvar.name='cornerx'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = cornerobject
            target.data_path = 'bound_box[0][0]'

    def addYDriver(self, top, obj, wallobject, path, expression, cornerobject):
        fcurve = obj.driver_add('location', 1)
        fcurve.driver.expression = expression

        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = path

        dvar = fcurve.driver.variables.new()
        dvar.name='piecewidth'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'dimensions[1]'
        
        if cornerobject != None:
            dvar = fcurve.driver.variables.new()
            dvar.name='cornery'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = cornerobject
            target.data_path = 'bound_box[7][1]'
            
     #for floors
    def addXScaleDriver(self, top, obj, wallobject, toppath, expression, cornerobject):
        fcurve = obj.driver_add('scale', 0)
        fcurve.driver.expression = expression

        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = toppath

        dvar = fcurve.driver.variables.new()
        dvar.name='piecewidth'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'dimensions[1]'

        dvar = fcurve.driver.variables.new()
        dvar.name='wallthickness'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'bound_box[0][0]'
        
        if cornerobject != None:
            dvar = fcurve.driver.variables.new()
            dvar.name='cornerx'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = cornerobject
            target.data_path = 'bound_box[0][0]'

     #for floors
    def addYScaleDriver(self, top, obj, wallobject, toppath, expression, cornerobject):
        fcurve = obj.driver_add('scale', 1)
        fcurve.driver.expression = expression

        dvar = fcurve.driver.variables.new()
        dvar.name='count'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = top
        target.data_path = toppath

        dvar = fcurve.driver.variables.new()
        dvar.name='piecewidth'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'dimensions[1]'

        dvar = fcurve.driver.variables.new()
        dvar.name='wallthickness'
        dvar.type='SINGLE_PROP'
        target = dvar.targets[0]
        target.id = wallobject
        target.data_path = 'bound_box[0][0]'
        
        if cornerobject != None:
            dvar = fcurve.driver.variables.new()
            dvar.name='cornerx'
            dvar.type='SINGLE_PROP'
            target = dvar.targets[0]
            target.id = cornerobject
            target.data_path = 'bound_box[2][1]'

      
    def addTallArray(self, obj, count, displace, absolute):
        mod = obj.modifiers.new("Tall", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = count
        if absolute:
            mod.use_relative_offset = False
            mod.use_constant_offset = True
            mod.constant_offset_displace = (0,0,displace)
        else:
            mod.relative_offset_displace = (0,0,displace)

  
    def execute(self, context):
        scene = bpy.context.scene
        
        nz = scene.buo_height
        nx = scene.buo_width
        ny = scene.buo_depth
        
        
        #print ("create building with "+str(object)+":"+str(nx)+" x "+str(ny)+" x "+str(nz))
        
        wallobject = context.scene.buo_WallObject
        walltop    = context.scene.buo_WallTop
        wallbottom = context.scene.buo_WallBottom

        cornerobject = context.scene.buo_Corner
        cornertop    = context.scene.buo_CornerTop
        cornerbottom = context.scene.buo_CornerBottom
        
        floors = context.scene.buo_Floors
        destructo = context.scene.buo_DestructoBall
        
        #print (str(wallobject.dimensions))
        wallx = wallobject.dimensions.x
        wally = wallobject.dimensions.y
        wallz = wallobject.dimensions.z
        
        #cornerx = 0
        #cornery = 0
        #if cornerobject != None:
        #    cornerx = cornerobject.dimensions.x
        #    cornery = cornerobject.dimensions.y
        
        #if wallbottom!=None:print('base bounding: '+str(wallbottom.bound_box))
            
        offsetz = 0
        if wallbottom != None: offsetz = wallbottom.dimensions[2]
        
        print ("create building with wall dims:"+str(wallx)+" x "+str(wally)+" x "+str(wallz))
        
        #-----------create walls
        frontwall = wallobject.copy() #links data, i think
        frontwall.name = "FrontWall"
        scene.objects.link(frontwall)

        backwall = wallobject.copy()
        backwall.name = "BackWall"
        scene.objects.link(backwall)
        
        leftwall = wallobject.copy()
        leftwall.name = "LeftWall"
        scene.objects.link(leftwall)
        
        rightwall = wallobject.copy()
        rightwall.name = "RightWall"
        scene.objects.link(rightwall)
        
        


        #-----------create parent
        bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=False)
        top = bpy.context.object
        top.name = "NewBuilding"
        #top['buo_object'] = True
        top['buo_tall'] = nz
        top['buo_wide'] = nx
        top['buo_deep'] = ny
        
        frontwall.parent = top
        backwall .parent = top
        leftwall .parent = top
        rightwall.parent = top
        
        frontwall.location = [(1-nx)*wally/2, -ny*wally/2, offsetz]
        backwall .location = [(1-nx)*wally/2,  ny*wally/2, offsetz]
        leftwall .location = [-nx*wally/2, (1-ny)*wally/2, offsetz]
        rightwall.location = [ nx*wally/2, (1-ny)*wally/2, offsetz]
        
        leftwall .rotation_euler = [0,0,radians(180)]
        rightwall.rotation_euler = [0,0,0]
        frontwall.rotation_euler = [0,0,-radians(90)]
        backwall .rotation_euler = [0,0,radians(90)]


         #----destructo object
        # add in a new sphere
        destructo_obj = None
        if destructo:
            bpy.ops.mesh.primitive_ico_sphere_add(size=1, view_align=False, enter_editmode=False, location=(top.location[0], top.location[1], offsetz + nz * wallz ))
            destructo_obj = bpy.context.object
            destructo_obj.name = "DestructoBool"
            destructo_obj.draw_type = 'BOUNDS'
            destructo_obj.hide_render = True


         
         #----front wall modifiers
        mod = frontwall.modifiers.new("Tall", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nz
        mod.relative_offset_displace = (0,0,1)
        if wallbottom != None: mod.start_cap = wallbottom
        if walltop    != None: mod.end_cap   = walltop

        mod = frontwall.modifiers.new("Wide", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nx
        mod.relative_offset_displace = (0,1,0)

        self.addTallDriver(top, frontwall)
        self.addCountDriver(top, frontwall, "Wide", '["buo_wide"]')
        self.addXDriver(top, frontwall, wallobject, '["buo_wide"]', "(1-count)* piecewidth/2", None)
        self.addYDriver(top, frontwall, wallobject, '["buo_deep"]', "-count*piecewidth/2 " + ("-cornery" if cornerobject != None else ""), cornerobject)

        if destructo:
            mod = frontwall.modifiers.new("Destruct", 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = destructo_obj


            

         #----back wall modifiers
        mod = backwall.modifiers.new("Tall", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nz
        mod.relative_offset_displace = (0,0,1)
        if wallbottom != None: mod.start_cap = wallbottom
        if walltop    != None: mod.end_cap   = walltop
        
        mod = backwall.modifiers.new("Wide", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nx
        mod.relative_offset_displace = (0,-1,0)
        
        self.addTallDriver(top, backwall)
        self.addCountDriver(top, backwall, "Wide", '["buo_wide"]')
        self.addXDriver(top, backwall, wallobject, '["buo_wide"]', "(1-count) * piecewidth/2", None)
        self.addYDriver(top, backwall, wallobject, '["buo_deep"]', "count*piecewidth/2 " + ("+cornery" if cornerobject != None else ""), cornerobject)

        if destructo:
            mod = backwall.modifiers.new("Destruct", 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = destructo_obj
            
        
         #----left wall modifiers        
        mod = leftwall.modifiers.new("Tall", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nz
        mod.relative_offset_displace = (0,0,1)
        if wallbottom != None: mod.start_cap = wallbottom
        if walltop    != None: mod.end_cap   = walltop
        
        mod = leftwall.modifiers.new("Wide", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = ny
        mod.relative_offset_displace = (0,-1,0)
       
        self.addTallDriver(top, leftwall)
        self.addCountDriver(top, leftwall, "Wide", '["buo_deep"]')
        self.addXDriver(top, leftwall, wallobject, '["buo_wide"]', "-count*piecewidth/2 " + ("+cornerx" if cornerobject != None else ""), cornerobject)
        self.addYDriver(top, leftwall, wallobject, '["buo_deep"]', "(1-count) * piecewidth/2", None)

        if destructo:
            mod = leftwall.modifiers.new("Destruct", 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = destructo_obj
            
       
        #----right wall modifiers 
        mod = rightwall.modifiers.new("Tall", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = nz
        mod.relative_offset_displace = (0,0,1)
        if wallbottom != None: mod.start_cap = wallbottom
        if walltop    != None: mod.end_cap   = walltop
        self.addTallDriver(top, rightwall)
        
        mod = rightwall.modifiers.new("Wide", 'ARRAY')
        mod.use_merge_vertices = True
        mod.merge_threshold = 0.001
        mod.count = ny
        mod.relative_offset_displace = (0,1,0)

        self.addTallDriver(top, rightwall)
        self.addCountDriver(top, rightwall, "Wide", '["buo_deep"]')
        self.addXDriver(top, rightwall, wallobject, '["buo_wide"]', "count*piecewidth/2 " + ("-cornerx" if cornerobject != None else ""), cornerobject)
        self.addYDriver(top, rightwall, wallobject, '["buo_deep"]', "(1-count) * piecewidth/2", None)

        if destructo:
            mod = rightwall.modifiers.new("Destruct", 'BOOLEAN')
            mod.operation = 'DIFFERENCE'
            mod.object = destructo_obj


        #----front right corner
        if cornerobject:
            frontrightcorner = cornerobject.copy() #links data, i think
            frontrightcorner.parent = top
            frontrightcorner.location[2] = offsetz
            frontrightcorner.name = "CornerFrontRight"
            scene.objects.link(frontrightcorner)
            
            mod = frontrightcorner.modifiers.new("Tall", 'ARRAY')
            mod.use_merge_vertices = True
            mod.merge_threshold = 0.001
            mod.count = nz
            mod.relative_offset_displace = (0,0,1)
            
            self.addTallDriver(top, frontrightcorner)
            self.addXDriver(top, frontrightcorner, wallobject, '["buo_wide"]', "count*piecewidth/2 " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYDriver(top, frontrightcorner, wallobject, '["buo_deep"]', "-count*piecewidth/2 " + ("-cornery" if cornerobject != None else ""), cornerobject)

            if wallbottom != None: mod.start_cap = cornerbottom
            if walltop    != None: mod.end_cap   = cornertop

            if destructo:
                mod = frontrightcorner.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            
            
        #----front left corner
            frontleftcorner = cornerobject.copy() #links data, i think
            frontleftcorner.parent = top
            frontleftcorner.location[2] = offsetz
            frontleftcorner.scale[0] = -1
            frontleftcorner.name = "CornerFrontLeft"
            scene.objects.link(frontleftcorner)
            
            mod = frontleftcorner.modifiers.new("Tall", 'ARRAY')
            mod.use_merge_vertices = True
            mod.merge_threshold = 0.001
            mod.count = nz
            mod.relative_offset_displace = (0,0,1)
            
            self.addTallDriver(top, frontleftcorner)
            self.addXDriver(top, frontleftcorner, wallobject, '["buo_wide"]', "-(count*piecewidth/2 " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYDriver(top, frontleftcorner, wallobject, '["buo_deep"]', "-count*piecewidth/2 " + ("-cornery" if cornerobject != None else ""), cornerobject)

            if wallbottom != None: mod.start_cap = cornerbottom
            if walltop    != None: mod.end_cap   = cornertop

            if destructo:
                mod = frontleftcorner.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            
            
         #----back right corner
            backrightcorner = cornerobject.copy() #links data, i think
            backrightcorner.parent = top
            backrightcorner.scale[1] = -1
            #backrightcorner.scale[0] = -1
            backrightcorner.location[2] = offsetz
            backrightcorner.name = "CornerBackRight"
            scene.objects.link(backrightcorner)
            
            mod = backrightcorner.modifiers.new("Tall", 'ARRAY')
            mod.use_merge_vertices = True
            mod.merge_threshold = 0.001
            mod.count = nz
            mod.relative_offset_displace = (0,0,1)
            
            self.addTallDriver(top, backrightcorner)
            self.addXDriver(top, backrightcorner, wallobject, '["buo_wide"]', "count*piecewidth/2 " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYDriver(top, backrightcorner, wallobject, '["buo_deep"]', "-(-count*piecewidth/2 " + ("-cornery" if cornerobject != None else ""), cornerobject)

            if wallbottom != None: mod.start_cap = cornerbottom
            if walltop    != None: mod.end_cap   = cornertop

            if destructo:
                mod = backrightcorner.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            
            
        #----back left corner
            backleftcorner = cornerobject.copy() #links data, i think
            backleftcorner.parent = top
            backleftcorner.location[2] = offsetz
            backleftcorner.scale[0] = -1
            backleftcorner.scale[1] = -1
            backleftcorner.name = "CornerBackLeft"
            scene.objects.link(backleftcorner)
            
            mod = backleftcorner.modifiers.new("Tall", 'ARRAY')
            mod.use_merge_vertices = True
            mod.merge_threshold = 0.001
            mod.count = nz
            mod.relative_offset_displace = (0,0,1)
            
            self.addTallDriver(top, backleftcorner)
            self.addXDriver(top, backleftcorner, wallobject, '["buo_wide"]', "-(count*piecewidth/2 " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYDriver(top, backleftcorner, wallobject, '["buo_deep"]', "-(-count*piecewidth/2 " + ("-cornery" if cornerobject != None else ""), cornerobject)

            if wallbottom != None: mod.start_cap = cornerbottom
            if walltop    != None: mod.end_cap   = cornertop

            if destructo:
                mod = backleftcorner.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            

        #---------floors
        if floors:
            bpy.ops.mesh.primitive_cube_add(radius=1, view_align=False, enter_editmode=False, location=(0, 0, offsetz ))
            floor = bpy.context.object
            floor.name = "Floors"
            floor.scale = (1,1, wallobject.dimensions[2]*.05)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            floor.parent = top
            if context.scene.buo_FloorMaterial != None:
                floor.data.materials.append(context.scene.buo_FloorMaterial)
            self.addTallArray(floor, nz, wallobject.dimensions[2], True)
            self.addTallDriver(top, floor, True)                         #the .99 is just a fudge to prevent annoying viewport artifacts for super skinny walls
            self.addXScaleDriver(top, floor, wallobject, '["buo_wide"]', ".99* ((count)* piecewidth/2) - abs(wallthickness) " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYScaleDriver(top, floor, wallobject, '["buo_deep"]', ".99* ((count)* piecewidth/2) - abs(wallthickness) " + ("+cornery" if cornerobject != None else ""), cornerobject)

            if destructo:
                mod = floor.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            
            bpy.ops.mesh.primitive_cube_add(radius=1, view_align=False, enter_editmode=False, location=(0, 0, offsetz ))
            roof = bpy.context.object
            roof.name = "Roof"
            roof.scale = (1,1, wallobject.dimensions[2]*.05)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            roof.parent = top
            if context.scene.buo_RoofMaterial != None:
                roof.data.materials.append(context.scene.buo_RoofMaterial)
            self.addRoofZDriver(top, roof, wallobject, walltop, wallbottom)
            self.addXScaleDriver(top, roof, wallobject, '["buo_wide"]', ".99* ((count)* piecewidth/2) - abs(wallthickness) " + ("-cornerx" if cornerobject != None else ""), cornerobject)
            self.addYScaleDriver(top, roof, wallobject, '["buo_deep"]', ".99* ((count)* piecewidth/2) - abs(wallthickness) " + ("+cornery" if cornerobject != None else ""), cornerobject)

            if destructo:
                mod = roof.modifiers.new("Destruct", 'BOOLEAN')
                mod.operation = 'DIFFERENCE'
                mod.object = destructo_obj
            

        #add armature controller    
        bpy.ops.object.armature_add(view_align=False, enter_editmode=False, location=(0,0,0))
        armature = bpy.context.object
        armature.name = "BuildingController"
        armature.parent = top
        armature.pose.bones[0].name = "DimsWidget"
        armature.location[2] = offsetz
        #armature.pose.bones["DimsWidget"].location = (...)
        self.addBoneDriver(top, armature, 0, wallobject, 'dimensions[1]')
        self.addBoneDriver(top, armature, 1, wallobject, 'dimensions[1]')
        self.addBoneDriver(top, armature, 2, wallobject, 'dimensions[2]')
        
        armature.pose.bones[0].location.x = nx * wally/2
        armature.pose.bones[0].location.z = ny * wally/2
        armature.pose.bones[0].location.y = (nz+1) * wallz




        # set context to the parent empty
        bpy.context.scene.objects.active = top

        
        return{'FINISHED'} 
    


#class BUO_WallCreateData():
#    width  = bpy.props.IntProperty(name="Width", description="Array number wide", default=3, min=1)
#    depth  = bpy.props.IntProperty(name="Depth", description="Array number deep", default=3, min=1)
#    height = bpy.props.IntProperty(name="Height",description="Array number tall", default=4, min=1)
#    wall_object = bpy.props.PointerProperty(
#            type = bpy.types.Object,
#            poll = BUO_WallMeshObject_poll
#        )


def register():
    bpy.utils.register_class(BuildOutPanel)
    bpy.utils.register_class(BUO_CreateWallOperator)
    
    bpy.types.Scene.buo_WallObject = bpy.props.PointerProperty(
            name = "Wall obj",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )
    bpy.types.Scene.buo_WallTop = bpy.props.PointerProperty(
            name = "Wall top",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )
    bpy.types.Scene.buo_WallBottom = bpy.props.PointerProperty(
            name = "Wall bottom",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )

    bpy.types.Scene.buo_Corner = bpy.props.PointerProperty(
            name = "Corner obj",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )
    bpy.types.Scene.buo_CornerTop = bpy.props.PointerProperty(
            name = "Top Corner",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )
    bpy.types.Scene.buo_CornerBottom = bpy.props.PointerProperty(
            name = "Bottom Corner",
            type = bpy.types.Object,
            poll = BUO_WallMeshObject_poll
        )
        
    bpy.types.Scene.buo_Floors = bpy.props.BoolProperty(name="Floors", description="Whether to generate floors", default=False)
    bpy.types.Scene.buo_FloorMaterial = bpy.props.PointerProperty(
            name = "Floor Material",
            type = bpy.types.Material,
            #poll = BUO_WallMeshObject_poll
        )
    bpy.types.Scene.buo_RoofMaterial = bpy.props.PointerProperty(
            name = "Roof Material",
            type = bpy.types.Material,
            #poll = BUO_WallMeshObject_poll
        )

    bpy.types.Scene.buo_DestructoBall = bpy.props.BoolProperty(name="Destructo-ball", description="Attach a boolean to generated objects", default=False)

    bpy.types.Scene.buo_width  = bpy.props.IntProperty(name="Width", description="Array number wide", default=3, min=1)
    bpy.types.Scene.buo_depth  = bpy.props.IntProperty(name="Depth", description="Array number deep", default=3, min=1)
    bpy.types.Scene.buo_height = bpy.props.IntProperty(name="Height",description="Array number tall", default=4, min=1)

    # addon updater code and configurations
    #addon_updater_ops.register(bl_info)


def unregister():
    bpy.utils.unregister_class(BUO_CreateWallOperator)
    #bpy.utils.unregister_class(BUO_WallCreateData)
    bpy.utils.unregister_class(BuildOutPanel)
    
    del bpy.types.Scene.buo_WallObject
    del bpy.types.Scene.buo_WallTop
    del bpy.types.Scene.buo_WallBottom
    
    del bpy.types.Scene.buo_Corner
    del bpy.types.Scene.buo_CornerTop
    del bpy.types.Scene.buo_CornerBottom
    
    del bpy.types.Scene.buo_width
    del bpy.types.Scene.buo_depth
    del bpy.types.Scene.buo_height
    
    del bpy.types.Scene.buo_Floors
    del bpy.types.Scene.buo_FloorMaterial
    del bpy.types.Scene.buo_RoofMaterial
    del bpy.types.Scene.buo_DestructoBall
        

