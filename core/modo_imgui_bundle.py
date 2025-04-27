#####################################################################################################################
# Modo Imgui Bundle - Core
# Author: Nikolas Sumnall
# Date: 2025-04-26
# Description: This kit creates a custom Modo pane using PySide6 and OpenGL to render an ImGui Bundle interface.
# License: MIT
#####################################################################################################################
# PYTHON
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
    def __init__(self, render_loop_function, parent=None):
        super().__init__(parent)
        self._render_loop_function = render_loop_function
        self.setMouseTracking(True)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self._set_refresh_rate()

    def _set_refresh_rate(self):
        """Set the refresh rate of the UI."""
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000 // int(UI_REFRESH_RATE))

    def initializeGL(self):
        """Initialize the OpenGL context."""
        gl.glClearColor(0.1, 0.1, 0.1, 1.0)
        imgui.create_context()
        try:
            imgui.backends.opengl3_init("#version 330")
        except:
            imgui.backends.opengl3_shutdown()
            imgui.backends.opengl3_init("#version 330")
        imgui.backends.opengl3_new_frame()
        imgui.get_io().display_size = imgui.ImVec2(self.width(), self.height())

    def resizeGL(self, width, height):
        """Handle window resizing."""
        gl.glViewport(0, 0, width, height)
        imgui.get_io().display_size = imgui.ImVec2(width, height)

    def paintGL(self):
        """Execute the loop and render backend."""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self._render_loop_function()
        imgui.backends.opengl3_render_draw_data(imgui.get_draw_data())

    def deleteLater(self):
        """Clean up the OpenGL context."""
        imgui.backends.opengl3_shutdown()
        imgui.destroy_context()
        return super().close()

    def mouseMoveEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse move events."""
        imgui_io = imgui.get_io()
        imgui_io.mouse_pos = imgui.ImVec2(event.position().x(), event.position().y())
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse press events."""
        imgui_io = imgui.get_io()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            imgui_io.mouse_down[0] = True
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            imgui_io.mouse_down[1] = True
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            imgui_io.mouse_down[2] = True
        super().mousePressEvent(event)


    def mouseReleaseEvent(self, event: QtGui.QMouseEvent):
        """Handle mouse release events."""
        imgui_io = imgui.get_io()
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            imgui_io.mouse_down[0] = False
        elif event.button() == QtCore.Qt.MouseButton.RightButton:
            imgui_io.mouse_down[1] = False
        elif event.button() == QtCore.Qt.MouseButton.MiddleButton:
            imgui_io.mouse_down[2] = False
        super().mouseReleaseEvent(event)


    def wheelEvent(self, event: QtGui.QWheelEvent):
        """Handle mouse wheel events."""
        imgui_io = imgui.get_io()
        scroll_amount = event.angleDelta().y() / 120.0
        imgui_io.mouse_wheel += scroll_amount
        super().wheelEvent(event)


    def keyPressEvent(self, event: QtGui.QKeyEvent):
        """Handle key press events."""
        imgui_io = imgui.get_io()
        key = event.key()
        if 0 <= key < 512:
            imgui_io.add_key_event(key, True)
        imgui_io.key_ctrl = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        imgui_io.key_shift = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
        imgui_io.key_alt = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier)
        if event.text():
            for char in event.text():
                imgui_io.add_input_character(ord(char))
        super().keyPressEvent(event)


    def keyReleaseEvent(self, event: QtGui.QKeyEvent):
        """Handle key release events."""
        imgui_io = imgui.get_io()
        key = event.key()
        if 0 <= key < 512:
            imgui_io.add_key_event(key, False)
        imgui_io.key_ctrl = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier)
        imgui_io.key_shift = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier)
        imgui_io.key_alt = bool(event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier)
        super().keyReleaseEvent(event)


#####################################################################################################################


class MIBView(lxifc.CustomView):
    """Custom view Imgui Bundle base class."""
    def __init__(self, window: 'MIBRenderLoop'):
        super().__init__()
        self._render_loop_function = window.render_loop

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
            self._widget = MIBOGLWidget(self._render_loop_function, parent_widget)
            layout.addWidget(self._widget)
            return True
        return False
    
    def customview_Cleanup(self, pane):
        """Clean up the custom view."""
        self._widget.deleteLater()
        return super().customview_Cleanup(pane)


class MIBRenderLoop:
    """Custom window Imgui Bundle base class."""

    def render_loop(self):
        """Override this method to implement your render loop."""
        raise NotImplementedError("Implement render loop!")