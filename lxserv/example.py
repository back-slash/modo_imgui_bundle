#####################################################################################################################
# Modo Imgui Bundle - Example
# Author: Nikolas Sumnall
# Date: 2025-04-26
# Description: Example customview and command for Modo Imgui Bundle.
# License: MIT
##################################################################################################################### 
# PYTHON
import site
import traceback

# MODO
import lx
import lxu.command as lxuc

#KIT
try:
    fileService = lx.service.File()
    aliasPath = fileService.ToLocalAlias('resource:')
    site.addsitedir(f"{aliasPath}/python3kit/extra64/Python/Lib/site-packages")
    from imgui_bundle import imgui
    import core.modo_imgui_bundle as cmib
except:
    lx.out(traceback.format_exc())
#####################################################################################################################




class MIBExampleRenderLoop(cmib.MIBRenderLoop):
    def __init__(self):
        self._choice = 0

    def render_loop(self):
        io = imgui.get_io()
        window_width = io.display_size.x
        window_height = io.display_size.y
        imgui.new_frame()
        imgui.set_next_window_size((window_width, window_height))
        imgui.set_next_window_pos((0, 0))
        window_flags = imgui.WindowFlags_.no_resize | imgui.WindowFlags_.no_move | imgui.WindowFlags_.no_scrollbar
        imgui.begin("Modo Imgui Bundle Example", False, window_flags)
        imgui.text("Hello, User!")
        imgui.text("This is a simple example of how to use Imgui Bundle in modo.")
        imgui.set_next_item_width(200)
        item_list = ["mesh", "camera", "light", "locator"]
        _, self._choice = imgui.combo("Select Item Type:", self._choice, item_list)
        imgui.same_line()
        if imgui.button("Create Modo Object"):
            lx.eval(f"item.create {item_list[self._choice]}")
        imgui.end()
        imgui.render()        


class MIBExampleView(cmib.MIBView):
    def __init__(self):
        window = MIBExampleRenderLoop()
        super().__init__(window)


class MIBExampleCommand(lxuc.BasicCommand):
    def __init__(self):
        super().__init__()
    
    @cmib.modo_error_out
    def basic_Execute(self, msg, flags):
        lx.eval('layout.createOrClose cookie:mib_example_cookie layout:mib_example_layout width:1280 height:720')


#####################################################################################################################

@cmib.modo_error_out
def bless_classes():
    lx.out("Blessing classes...")
    lx.bless(MIBExampleView, "Modo Imgui Bundle Example")
    lx.bless(MIBExampleCommand, "mib_example_command.open")

bless_classes()