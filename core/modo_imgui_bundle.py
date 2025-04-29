#####################################################################################################################
# Modo ImGui Bundle - Core
# Author: Nikolas Sumnall
# Date: 2025-04-27
# Description: This kit creates a custom Modo pane using PySide6 and OpenGL to render an ImGui Bundle interface.
# License: MIT
#####################################################################################################################
# PYTHON
from multiprocessing import context
import site
import traceback

# MODO
import lx
import lxifc
from PySide6 import QtWidgets, QtCore, QtGui, QtOpenGLWidgets

#KIT
try:
    fileService = lx.service.File()
    aliasPath = fileService.ToLocalAlias('resource:')
    site.addsitedir(f"{aliasPath}/python3kit/extra64/Python/Lib/site-packages")
    import OpenGL.GL as gl
    from imgui_bundle import imgui
except:
	lx.out(traceback.format_exc())

#####################################################################################################################
UI_REFRESH_RATE = 60
#####################################################################################################################

def modo_error_out(func):
    """Decorator that prints the traceback of the last exception."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exception:
            lx.out(f"Error: {str(exception)}")
            lx.out(traceback.format_exc())
            raise
    return wrapper

#####################################################################################################################

class MIBOGLWidget(QtOpenGLWidgets.QOpenGLWidget):
    """OpenGL widget for rendering ImGui."""
    def __init__(self, render_loop_class: 'MIBRenderLoop', parent=None):
        super().__init__(parent)
        self._init_render_context_manager(render_loop_class)
        self._set_refresh_rate()
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

    def _init_render_context_manager(self, render_loop_class: 'MIBRenderLoop'):
        self._render_context_manger = MIBRenderContextManager()
        self._context = self._render_context_manger.context_list[-1]
        self._render_loop_function = render_loop_class(self._context).render_loop

    def _set_refresh_rate(self):
        """Set the refresh rate of the UI."""
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // int(UI_REFRESH_RATE))

    def initializeGL(self):
        """Initialize the OpenGL context."""
        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        imgui.set_current_context(self._context)
        imgui.backends.opengl3_new_frame()
        imgui.get_io().display_size = imgui.ImVec2(self.width(), self.height())

    def resizeGL(self, width, height):
        """Handle window resizing."""
        gl.glViewport(0, 0, width, height)
        imgui.set_current_context(self._context)
        imgui.get_io().display_size = imgui.ImVec2(width, height)

    def paintGL(self):
        """Execute the loop and render backend."""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._render_loop_function()
        imgui.backends.opengl3_render_draw_data(imgui.get_draw_data())

    def deleteLater(self):
        """Override deleteLater to clean up the context."""
        self._render_context_manger.remove_context(self._context)
        return super().deleteLater()
    

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse move events."""
        imgui.set_current_context(self._context)
        imgui.get_io().mouse_pos = imgui.ImVec2(event.position().x(), event.position().y())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse press events."""
        imgui.set_current_context(self._context)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            imgui.get_io().mouse_down[0] = True
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            imgui.get_io().mouse_down[1] = True
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            imgui.get_io().mouse_down[2] = True
        super().mousePressEvent(event)


    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse release events."""
        imgui.set_current_context(self._context)
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            imgui.get_io().mouse_down[0] = False
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            imgui.get_io().mouse_down[1] = False
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            imgui.get_io().mouse_down[2] = False
        super().mouseReleaseEvent(event)


    def wheelEvent(self, event: QtGui.QWheelEvent):
        """Handle mouse wheel events."""
        imgui.set_current_context(self._context)
        scroll_amount = event.angleDelta().y() / 120.0
        imgui.get_io().mouse_wheel += scroll_amount
        super().wheelEvent(event)


    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """Handle key press events."""
        imgui.set_current_context(self._context)
        key = event.key()
        if 0 <= key < 512:
            imgui.get_io().add_key_event(key, True)
        imgui.get_io().key_ctrl = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        imgui.get_io().key_shift = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
        imgui.get_io().key_alt = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier)
        if event.text():
            for char in event.text():
                imgui.get_io().add_input_character(ord(char))
        super().keyPressEvent(event)


    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        """Handle key release events."""
        imgui.set_current_context(self._context)
        key = event.key()
        if 0 <= key < 512:
            imgui.get_io().add_key_event(key, False)
        imgui.get_io().key_ctrl = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        imgui.get_io().key_shift = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
        imgui.get_io().key_alt = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier)
        super().keyReleaseEvent(event)


#####################################################################################################################


class MIBView(lxifc.CustomView):
    """Custom view ImGui Bundle base class."""
    def __init__(self, render_loop_class: 'MIBRenderLoop'):
        super().__init__()
        self._render_loop_class = render_loop_class
        
    def customview_Init(self, pane):
        if pane == None:
            return False
        custPane = lx.object.CustomPane(pane)
        if custPane.test() == False:
            return False
        parent_pane = custPane.GetParent()
        parent_widget = lx.getQWidget(parent_pane)
        if parent_widget != None:
            layout = QtWidgets.QVBoxLayout(parent_widget)
            layout.setContentsMargins(0, 0, 0, 0)
            self._widget = MIBOGLWidget(self._render_loop_class, parent_widget)
            layout.addWidget(self._widget)
            return True
        return False
    
    def customview_Cleanup(self, pane):
        """Clean up the custom view."""
        self._widget.deleteLater()
        return super().customview_Cleanup(pane)


class MIBRenderLoop:
    """Custom window ImGui Bundle base class."""
    def __init__(self, context):
        self._context = context

    def render_loop(self):
        """Override this method to implement your render loop."""
        raise NotImplementedError("Implement render loop!")
    

class MIBRenderContextManager:
    """Render/Context manager for ImGui Bundle."""
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, 'context_list') and len(self.context_list) > 0:
            imgui.set_current_context(self.context_list[-1])
            self.context_list.append(imgui.create_context())
            self._init_renderer()
            return
        self.context_list = []
        self.context_list.append(imgui.create_context())   
        self._init_renderer()
    
    def _init_renderer(self):
        """Initialize the renderer."""
        imgui.set_current_context(self.context_list[-1])
        imgui.backends.opengl3_init("#version 330")

    def remove_context(self, context):
        """Remove a context from the context list."""
        if context in self.context_list:
            self.context_list.remove(context)
            imgui.set_current_context(context)
            imgui.backends.opengl3_shutdown()
            imgui.destroy_context(context)