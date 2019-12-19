from OpenGL.GL import *
from OpenGL.GLU import *

import numpy


def assert_int(val):
    if not isinstance(val, int):
        raise ValueError("value is not an int: {}".format(val))


def pad_or_trunc(l, length):
    if len(l) < length:
        return l + [0] * (length - len(l))
    else:
        return l[:length]


def remove_all_in_place(l, elements):
    if len(l) == 0:
        return l

    rem_set = set(elements)
    last_element = len(l) - 1
    i = 0

    while i <= last_element:
        if l[i] in rem_set:
            while i <= last_element and l[last_element] in rem_set:
                last_element -= 1
            if i > last_element:
                break
            else:
                l[i] = l[last_element]
                last_element -= 1
        i += 1

    del l[(last_element+1):]


class _Layer:
    def __init__(self, name, layer_id, z_order, sort_sprites, use_color):
        """
            name: str -- used for logging
            z_order: number -- used to decide layer draw order
            sort_sprites: bool -- true if layer should sort sprites by depth
            use_color: bool -- true if layer respects sprites' color value
        """
        self.name = name
        self.layer_id = layer_id
        self.images = []  # ordered list of image ids
        self._image_set = set()
        self._offset = (0, 0)
        self._z_order = z_order
        self.sort_sprites = sort_sprites

        # these are the pointers the layer passes to gl
        self.vertices = numpy.array([], dtype=float)
        self.tex_coords = numpy.array([], dtype=float)
        self.indices = numpy.array([], dtype=float)
        self.colors = numpy.array([], dtype=float) if use_color else None
        
        self._dirty_sprites = []
        self._to_remove = []
        self._to_add = []
    
    def set_offset(self, x, y):
        self._offset = (x, y)

    def offset(self):
        return self._offset
    
    def update(self, bundle_id):
        assert_int(bundle_id)
        if bundle_id in self._image_set:
            self._dirty_sprites.append(bundle_id)
        else:
            self._image_set.add(bundle_id)
            self._to_add.append(bundle_id)
        
    def remove(self, bundle_id):
        assert_int(bundle_id)
        if bundle_id in self._image_set:
            self._image_set.remove(bundle_id)
            self._to_remove.append(bundle_id)
        
    def is_dirty(self):
        return len(self._dirty_sprites) + len(self._to_add) + len(self._to_remove) > 0
        
    def uses_color(self):
        return self.colors is not None
        
    def rebuild(self, bundle_lookup): 
        if len(self._to_remove) > 0:
            for bun_id in self._to_remove:
                if bun_id in self._image_set:
                    self._image_set.remove(bun_id)

            remove_all_in_place(self.images, self._to_remove)
            remove_all_in_place(self._to_add, self._to_remove)
            self._to_remove.clear()

        if len(self._to_add) > 0:
            self.images.extend(self._to_add)
            self._to_add.clear()

        self._dirty_sprites.clear()
        
        if self.sort_sprites:
            self.images.sort(key=lambda x: -bundle_lookup[x].depth())

        n_sprites = len(self.images)

        # need refcheck to be false or else Pycharm's debugger can cause this to fail (due to holding a ref)
        self.vertices.resize(8 * n_sprites, refcheck=False)
        self.tex_coords.resize(8 * n_sprites, refcheck=False)
        self.indices.resize(6 * n_sprites, refcheck=False)
        if self.uses_color():
            self.colors.resize(4 * 3 * n_sprites, refcheck=False)

        for i in range(0, n_sprites):
            bundle = bundle_lookup[self.images[i]]
            bundle.add_urself(
                    i,
                    self.vertices, 
                    self.tex_coords, 
                    self.colors, 
                    self.indices)
            
    def render(self, engine):
        # split up like this to make it easier to find performance bottlenecks
        self._set_client_states(True, engine)
        self._pass_attributes(engine)
        self._draw_elements()
        self._set_client_states(False, engine)

    def _set_client_states(self, enable, engine):
        engine.set_vertices_enabled(enable)
        engine.set_texture_coords_enabled(enable)
        if self.uses_color():
            engine.set_colors_enabled(enable)

    def _pass_attributes(self, engine):
        engine.set_vertices(self.vertices)
        engine.set_texture_coords(self.tex_coords)
        if self.uses_color():
            engine.set_colors(self.colors)

    def _draw_elements(self):
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)

    def __len__(self):
        return len(self.images)   
        
    def __contains__(self, uid):
        return uid in self._image_set
        
    def z_order(self):
        return self._z_order

    def num_sprites(self):
        return len(self.images)


def printOpenGLError():
    err = glGetError()
    if (err != GL_NO_ERROR):
        print("GLERROR: {}".format(gluErrorString(err)))


class Shader:

    def __init__(self, vertex_shader_source, fragment_shader_source):
        self.program = glCreateProgram()
        printOpenGLError()

        self.vs = glCreateShader(GL_VERTEX_SHADER)
        glShaderSource(self.vs, [vertex_shader_source])
        glCompileShader(self.vs)
        glAttachShader(self.program, self.vs)
        printOpenGLError()
        info_log = glGetShaderInfoLog(self.vs)
        if len(info_log) > 0:
            print("INFO: vertex shader has non-empty info log: {}".format(info_log))

        self.fs = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource(self.fs, [fragment_shader_source])
        glCompileShader(self.fs)
        glAttachShader(self.program, self.fs)
        printOpenGLError()
        info_log = glGetShaderInfoLog(self.fs)
        if len(info_log) > 0:
            print("INFO: fragment shader has non-empty info log: {}".format(info_log))

        glLinkProgram(self.program)
        printOpenGLError()

    def get_program(self):
        return self.program

    def begin(self):
        if glUseProgram(self.program):
            printOpenGLError()

    def end(self):
        glUseProgram(0)


_SINGLETON = None


class RenderEngine:

    @staticmethod
    def create_instance():
        """intializes the RenderEngine singleton."""
        global _SINGLETON
        if _SINGLETON is not None:
            raise ValueError("There is already a RenderEngine initialized.")
        else:
            _SINGLETON = RenderEngine130()
            return _SINGLETON

    @staticmethod
    def get_instance():
        """after init is called, returns the RenderEngine singleton."""
        return _SINGLETON

    def __init__(self):
        self.bundles = {}  # (int) id -> bundle
        self.camera_pos = [0, 0]
        self.size = (0, 0)
        self.min_size = (0, 0)
        self._pixel_mult = 1  # the number of screen "pixels" per game pixel
        self.layers = {}  # layer_id -> layer
        self.hidden_layers = {}  # layer_id -> None
        self.ordered_layers = []
        self.shader = None

        self.tex_id = None

        self.raw_texture_data = (None, 0, 0)  # data, width, height
        
    def add_layer(self, layer_id, layer_name, z_order, sort_sprites, use_color):
        l = _Layer(layer_name, layer_id, z_order, sort_sprites, use_color)
        self.layers[layer_id] = l
        
        self.ordered_layers = list(self.layers.values())
        self.ordered_layers.sort(key=lambda x: x.z_order())
        
    def remove_layer(self, layer_id):
        del self.layers[layer_id]
        
        self.ordered_layers = list(self.layers.values())
        self.ordered_layers.sort(key=lambda x: x.z_order())

    def hide_layer(self, layer_id):
        self.hidden_layers[layer_id] = None

    def show_layer(self, layer_id):
        if layer_id in self.hidden_layers:
            del self.hidden_layers[layer_id]
        
    def set_layer_offset(self, layer_id, offs_x, offs_y):
        self.layers[layer_id].set_offset(offs_x, offs_y)
        
    def clear_all_sprites(self):
        for uid in self.bundles:
            for l in self.layers.values():
                l.remove(uid)
        self.bundles.clear()
        
    def clear_bundles(self, bundles):
        for bun in bundles:
            self.remove(bun)

    def resize(self, w, h, px_scale=None):
        if px_scale is not None:
            self._pixel_mult = px_scale
        self.size = (max(w, self.min_size[0]),
                     max(h, self.min_size[1]))
        self.resize_internal()

    def set_min_size(self, w, h):
        self.min_size = (w, h)

        if self.size[0] < self.min_size[0] or self.size[1] < self.min_size[1]:
            self.resize(self.size[0], self.size[1])

    def get_game_size(self):
        return (int(self.size[0] / self.get_pixel_mult()),
                int(self.size[1] / self.get_pixel_mult()))

    def set_clear_color(self, r, g, b):
        """
            params: ints r,g,b in range [0, 255]
        """
        glClearColor(r / 255, g / 255, b / 255, 0.0)

    def get_pixel_mult(self):
        return self._pixel_mult

    def set_pixel_mult(self, val):
        self.resize(self.size[0], self.size[1], px_scale=val)

    def get_glsl_version(self):
        raise NotImplementedError()

    def build_shader(self):
        raise NotImplementedError()

    def setup_shader(self):
        raise NotImplementedError()

    def set_matrix_offset(self, x, y):
        raise NotImplementedError()

    def resize_internal(self):
        raise NotImplementedError()

    def set_vertices_enabled(self, val):
        raise NotImplementedError()

    def set_vertices(self, data):
        raise NotImplementedError()

    def set_texture_coords_enabled(self, val):
        raise NotImplementedError()

    def set_texture_coords(self, data):
        raise NotImplementedError()

    def set_colors_enabled(self, val):
        raise NotImplementedError()

    def set_colors(self, data):
        raise NotImplementedError()

    def get_shader(self):
        return self.shader

    def init(self, w, h):
        glShadeModel(GL_FLAT)
        glClearColor(0.5, 0.5, 0.5, 0.0)
        
        vstring = glGetString(GL_VERSION)
        vstring = vstring.decode() if vstring is not None else None
        print("INFO: running OpenGL version: {}".format(vstring))

        print("INFO: building shader for GLSL version: {}".format(self.get_glsl_version()))
        self.shader = self.build_shader()
        self.shader.begin()
        self.setup_shader()

        self.resize(w, h)

    def reset_for_display_mode_change(self):
        """
           XXX on Windows, when pygame.display.set_mode is called, it seems to wipe away the active
           gl context, so we get around that by rebuilding the shader program and rebinding the texture...
        """
        self.shader.end()

        self.shader = self.build_shader()
        self.shader.begin()
        self.setup_shader()

        img_data, w, h = self.raw_texture_data
        if img_data is not None:
            self.set_texture(img_data, w, h, tex_id=self.tex_id)

        self.resize(self.size[0], self.size[1])

    def set_texture(self, img_data, width, height, tex_id=None):
        """
            img_data: image data in string RGBA format.
        """
        if tex_id is None:
            tex_id = glGenTextures(1)
            self.tex_id = tex_id

        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glEnable(GL_TEXTURE_2D)

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.raw_texture_data = (img_data, width, height)

        self.set_texture_internal()

    def set_texture_internal(self):
        pass

    def set_camera_pos(self, x, y, center=False):
        self.camera_pos[0] = x - (self.size[0] // 2) if center else 0
        self.camera_pos[1] = y - (self.size[1] // 2) if center else 0
        
    def remove(self, img_bundle):
        if img_bundle is None:
            return
            
        uid = img_bundle.uid()
        if uid in self.bundles:
            del self.bundles[img_bundle.uid()]

        self.layers[img_bundle.layer()].remove(uid)
        
    def update(self, img_bundle):
        if img_bundle is None:
            return

        for bun in img_bundle.all_bundles():
            uid = bun.uid()
            self.bundles[uid] = bun

            layer = self.layers[bun.layer()]
            layer.update(uid)
        
    def __contains__(self, key):
        try:
            return key.uid() in self.bundles
        except ValueError:
            return False
        
    def render_layers(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        for layer in self.ordered_layers:
            if layer.is_dirty():
                layer.rebuild(self.bundles)

            if layer.layer_id in self.hidden_layers:
                continue

            offs = layer.offset()

            self.set_matrix_offset(-offs[0], -offs[1])
            
            layer.render(self)

    def cleanup(self):
        self.shader.end()

    def count_sprites(self):
        res = 0
        for layer in self.layers.values():
            res += layer.num_sprites()
        return res


# TODO - welp, this doesn't work anymore

class RenderEngine110(RenderEngine):

    def __init__(self):
        super().__init__()

    def get_glsl_version(self):
        return "110"

    def build_shader(self):
        return Shader(
            '''
            #version 110
            varying vec2 vTexCoord;

            void main() {
                vTexCoord = gl_MultiTexCoord0.st;
                gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
                gl_FrontColor = gl_Color;
            }
            ''',
            '''
            #version 110
            uniform sampler2D tex0;

            varying vec2 vTexCoord;

            void main() {
                vec4 tcolor = texture2D(tex0, vTexCoord);
                for (int i = 0; i < 3; i++) {
                    if (tcolor[i] >= 0.99) {
                        gl_FragColor[i] = tcolor[i] * gl_Color[i];
                    } else {
                        gl_FragColor[i] = tcolor[i] * gl_Color[i] * gl_Color[i];                    
                    }
                }
                gl_FragColor.w = tcolor.w * gl_Color.w;
                
            }
            ''')

    def set_vertices_enabled(self, val):
        if val:
            glEnableClientState(GL_VERTEX_ARRAY)
        else:
            glDisableClientState(GL_VERTEX_ARRAY)

    def set_vertices(self, data):
        glVertexPointer(2, GL_FLOAT, 0, data)

    def set_texture_coords_enabled(self, val):
        if val:
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        else:
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)

    def set_texture_coords(self, data):
        glTexCoordPointer(2, GL_FLOAT, 0, data)

    def set_colors_enabled(self, val):
        if val:
            glEnableClientState(GL_COLOR_ARRAY)
        else:
            glDisableClientState(GL_COLOR_ARRAY)

    def set_colors(self, data):
        glColorPointer(3, GL_FLOAT, 0, data)

    def setup_shader(self):
        glUniform1i(glGetUniformLocation(self.get_shader().get_program(), "tex0"), 0)

    def set_matrix_offset(self, x, y):
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(x, y, 0.0)

    def resize_internal(self):
        width, height = self.size
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, width, height, 0, 1, -1)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glViewport(0, 0, width, height)


def translation_matrix(x, y):
    res = numpy.identity(4, dtype=numpy.float32)
    res.itemset((0, 3), float(x))
    res.itemset((1, 3), float(y))
    return res


def ortho_matrix(left, right, bottom, top, near_val, far_val):
    res = numpy.identity(4, dtype=numpy.float32)
    res.itemset((0, 0), float(2 / (right - left)))
    res.itemset((1, 1), float(2 / (top - bottom)))
    res.itemset((2, 2), float(-2 / (far_val - near_val)))

    t_x = -(right + left) / (right - left)
    t_y = -(top + bottom) / (top - bottom)
    t_z = -(far_val + near_val) / (far_val - near_val)
    res.itemset((0, 3), float(t_x))
    res.itemset((1, 3), float(t_y))
    res.itemset((2, 3), float(t_z))

    return res


class RenderEngine130(RenderEngine):

    def __init__(self):
        super().__init__()
        self._tex_uniform_loc = None
        self._tex_size_uniform_loc = None
        self._modelview_matrix_uniform_loc = None
        self._proj_matrix_uniform_loc = None

        self._position_attrib_loc = None
        self._texture_pos_attrib_loc = None
        self._color_attrib_loc = None

        self._modelview_matrix = numpy.identity(4, dtype=numpy.float32)
        self._proj_matrix = numpy.identity(4, dtype=numpy.float32)

    def get_glsl_version(self):
        return "130"

    def build_shader(self):
        return Shader(
            '''
            # version 130
            in vec2 position;
            
            uniform mat4 modelview;
            uniform mat4 proj;
            
            in vec2 vTexCoord;
            out vec2 texCoord;
            
            in vec3 vColor;
            out vec3 color;
    
            void main()
            {
                texCoord = vTexCoord;
                color = vColor;
                gl_Position = proj * modelview * vec4(position.x, position.y, 0.0, 1.0);
            }
            ''',
            '''
            #version 130
            in vec2 texCoord;
            in vec3 color;
            
            uniform vec2 texSize;
            uniform sampler2D tex0;

            void main(void) {
                vec2 texPos = vec2(texCoord.x / texSize.x, texCoord.y / texSize.y);
                vec4 tcolor = texture2D(tex0, texPos);
                
                for (int i = 0; i < 3; i++) {
                    if (tcolor[i] >= 0.99) {
                        gl_FragColor[i] = tcolor[i] * color[i];
                    } else {
                        gl_FragColor[i] = tcolor[i] * color[i] * color[i];                    
                    }
                }
                
                gl_FragColor.w = tcolor.w;
            }
            '''
        )

    def _assert_valid_var(self, varname, loc):
        if loc < 0:
            raise ValueError("invalid uniform or attribute: {}".format(varname))

    def setup_shader(self):
        prog_id = self.get_shader().get_program()

        self._tex_uniform_loc = glGetUniformLocation(prog_id, "tex0")
        self._assert_valid_var("tex0", self._tex_uniform_loc)
        glUniform1i(self._tex_uniform_loc, 0)
        printOpenGLError()

        self._tex_size_uniform_loc = glGetUniformLocation(prog_id, "texSize")
        self._assert_valid_var("texSize", self._tex_size_uniform_loc)
        printOpenGLError()

        self._modelview_matrix_uniform_loc = glGetUniformLocation(prog_id, "modelview")
        self._assert_valid_var("modelview", self._modelview_matrix_uniform_loc)
        glUniformMatrix4fv(self._modelview_matrix_uniform_loc, 1, GL_TRUE, self._modelview_matrix)
        printOpenGLError()

        self._proj_matrix_uniform_loc = glGetUniformLocation(prog_id, "proj")
        self._assert_valid_var("proj", self._proj_matrix_uniform_loc)
        glUniformMatrix4fv(self._proj_matrix_uniform_loc, 1, GL_TRUE, self._proj_matrix)
        printOpenGLError()

        self._position_attrib_loc = glGetAttribLocation(prog_id, "position")
        self._assert_valid_var("position", self._position_attrib_loc)

        self._texture_pos_attrib_loc = glGetAttribLocation(prog_id, "vTexCoord")
        self._assert_valid_var("vTexCoord", self._texture_pos_attrib_loc)

        self._color_attrib_loc = glGetAttribLocation(prog_id, "vColor")
        self._assert_valid_var("vColor", self._color_attrib_loc)

        # set default color to white
        glVertexAttrib3f(self._color_attrib_loc, 1.0, 1.0, 1.0)
        printOpenGLError()

    def set_matrix_offset(self, x, y):
        self._modelview_matrix = numpy.identity(4, dtype=numpy.float32)
        trans = translation_matrix(x, y)
        numpy.matmul(self._modelview_matrix, trans, out=self._modelview_matrix, dtype=numpy.float32)

        glUniformMatrix4fv(self._modelview_matrix_uniform_loc, 1, GL_TRUE, self._modelview_matrix)
        printOpenGLError()

    def resize_internal(self):
        window_width, window_height = self.size
        game_width, game_height = self.get_game_size()

        self._proj_matrix = numpy.identity(4, dtype=numpy.float32)
        ortho = ortho_matrix(0, game_width, game_height, 0, 1, -1)
        numpy.matmul(self._proj_matrix, ortho, out=self._proj_matrix, dtype=numpy.float32)

        glUniformMatrix4fv(self._proj_matrix_uniform_loc, 1, GL_TRUE, self._proj_matrix)
        printOpenGLError()

        self.set_matrix_offset(0, 0)

        glViewport(0, 0, window_width, window_height)
        printOpenGLError()

        print("INFO: set window size to ({}, {}), game_size to ({}, {})".format(
            window_width, window_height, game_width, game_height))


    def set_texture_internal(self):
        if self.raw_texture_data is not None:
            tex_w = self.raw_texture_data[1]
            tex_h = self.raw_texture_data[2]

            glUniform2f(self._tex_size_uniform_loc, float(tex_w), float(tex_h))
            printOpenGLError()

    def set_vertices_enabled(self, val):
        if val:
            glEnableVertexAttribArray(self._position_attrib_loc)
        else:
            glDisableVertexAttribArray(self._position_attrib_loc)
        printOpenGLError()

    def set_vertices(self, data):
        glVertexAttribPointer(self._position_attrib_loc, 2, GL_FLOAT, GL_FALSE, 0, data)
        printOpenGLError()

    def set_texture_coords_enabled(self, val):
        if val:
            glEnableVertexAttribArray(self._texture_pos_attrib_loc)
        else:
            glDisableVertexAttribArray(self._texture_pos_attrib_loc)
        printOpenGLError()

    def set_texture_coords(self, data):
        glVertexAttribPointer(self._texture_pos_attrib_loc, 2, GL_FLOAT, GL_FALSE, 0, data)
        printOpenGLError()

    def set_colors_enabled(self, val):
        if val:
            glEnableVertexAttribArray(self._color_attrib_loc)
        else:
            glDisableVertexAttribArray(self._color_attrib_loc)
        printOpenGLError()

    def set_colors(self, data):
        glVertexAttribPointer(self._color_attrib_loc, 3, GL_FLOAT, GL_FALSE, 0, data)
        printOpenGLError()
