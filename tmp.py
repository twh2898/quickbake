import bpy

obj = bpy.context.active_object
# You can choose your texture size (This will be the de bake

assert obj is not None
assert obj.type == 'MESH'

image_name = obj.name + '_BakedTexture'
img = bpy.data.images.get(image_name)
if img is None:
    print('Creating new image')
    img = bpy.data.images.new(image_name, 1024, 1024)
else:
    print('Using existing image')

# Due to the presence of any multiple materials, it seems necessary to iterate on all the materials, and assign them a node + the image to bake.
for mat in obj.data.materials:

    mat.use_nodes = True  # Here it is assumed that the materials have been created with nodes, otherwise it would not be possible to assign a node for the Bake, so this step is a bit useless
    nodes = mat.node_tree.nodes
    texture_node = nodes.new('ShaderNodeTexImage')
    texture_node.name = 'Bake_node'
    texture_node.select = True
    nodes.active = texture_node
    texture_node.image = img  # Assign the image to the node

bpy.context.view_layer.objects.active = obj
bpy.ops.object.bake(type='DIFFUSE', save_mode='EXTERNAL')

img.save_render(filepath='C:\\TEMP\\baked.png')

# In the last step, we are going to delete the nodes we created earlier
for mat in obj.data.materials:
    for n in mat.node_tree.nodes:
        if n.name == 'Bake_node':
            mat.node_tree.nodes.remove(n)
