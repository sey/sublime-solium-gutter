import sublime
import sublime_plugin

import os, re, codecs, subprocess
try:
  import commands
except ImportError:
  pass

PLUGIN_FOLDER = os.path.dirname(os.path.realpath(__file__))

class SoliumGutterCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    # Make sure we're only linting Solidity files.
    if self.file_unsupported():
      return

    # Get the current text in the buffer and save it in a temporary file.
    # This allows for scratch buffers and dirty files to be linted as well.
    temp_file_path = self.save_buffer_to_temp_file()
    output = self.run_script_on_file(temp_file_path)
    os.remove(temp_file_path)

    # We're done with linting, rebuild the regions shown in the current view.
    SoliumGutterStore.reset()
    SoliumGutterEventListeners.reset()
    self.view.erase_regions("solium_errors")

    regions = []
    menuitems = []

    # For each line of Solium output (errors, warnings etc.) add a region
    # in the view and a menuitem in a quick panel.
    for line in output.splitlines():
      try:
        line_no, column_no, warning, message = line.split(":")
      except:
        continue

      hint_point = self.view.text_point(int(line_no) - 1, int(column_no if column_no != "NaN" else "1") - 1)
      hint_region = self.view.line(hint_point)
    
      regions.append(hint_region)
      menuitems.append(line_no + ":" + column_no + " " + message)
      SoliumGutterStore.errors.append((hint_region, message))

    self.add_regions(regions)
    self.view.window().show_quick_panel(menuitems, self.on_quick_panel_selection)

  def file_unsupported(self):
    file_path = self.view.file_name()
    view_settings = self.view.settings()
    has_sol_extension = file_path != None and bool(re.search(r'\.sol$', file_path))
    has_solidity_syntax = bool(re.search(r'Solidity', view_settings.get("syntax"), re.I))
    return (not has_sol_extension and not has_solidity_syntax)

  def save_buffer_to_temp_file(self):
    buffer_text = self.view.substr(sublime.Region(0, self.view.size()))
    temp_file_name = ".__temp__"
    temp_file_path = PLUGIN_FOLDER + "/" + temp_file_name
    f = codecs.open(temp_file_path, mode="w", encoding="utf-8")
    f.write(buffer_text)
    f.close()
    return temp_file_path

  def run_script_on_file(self, temp_file_path):
    # node_path = PluginUtils.get_node_path()
    script_path = PLUGIN_FOLDER + "/scripts/run.js"
    file_path = self.view.file_name()
    cmd = ['node', script_path, temp_file_path, file_path or "?"]
    output = SoliumGutterCommand.get_output(cmd)
    output = output.decode('utf-8');
    print(output)
    return output

  def add_regions(self, regions):
    package_name = (PLUGIN_FOLDER.split(os.path.sep))[-1]

    if int(sublime.version()) >= 3000:
      icon = "Packages/" + package_name + "/warning.png"
      self.view.add_regions("solium_errors", regions, "keyword", icon,
        sublime.DRAW_EMPTY |
        sublime.DRAW_NO_FILL |
        sublime.DRAW_NO_OUTLINE |
        sublime.DRAW_SQUIGGLY_UNDERLINE)
    else:
      icon = ".." + os.path.sep + package_name + os.path.sep + "warning"
      self.view.add_regions("solium_errors", regions, "keyword", icon,
        sublime.DRAW_EMPTY |
        sublime.DRAW_OUTLINED)

  def on_quick_panel_selection(self, index):
    if index == -1:
      return

    # Focus the user requested region from the quick panel.
    region = SoliumGutterStore.errors[index][0]
    region_cursor = sublime.Region(region.begin(), region.begin())
    selection = self.view.sel()
    selection.clear()
    selection.add(region_cursor)
    self.view.show(region_cursor)

  @staticmethod
  def get_output(cmd):
    if int(sublime.version()) < 3000:
      if sublime.platform() != "windows":
        # Handle Linux and OS X in Python 2.
        run = '"' + '" "'.join(cmd) + '"'
        return commands.getoutput(run)
      else:
        # Handle Windows in Python 2.
        # Prevent console window from showing.
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen(cmd, \
          stdout=subprocess.PIPE, \
          startupinfo=startupinfo).communicate()[0]
    else:
      # Handle all OS in Python 3.
      run = '"' + '" "'.join(cmd) + '"'
      try:
        return subprocess.check_output(run, stderr=subprocess.STDOUT, shell=True, env=os.environ)
      except Exception as exception:
        print(exception.output)

class SoliumGutterEventListeners(sublime_plugin.EventListener):
  timer = None

  @classmethod
  def reset(self):
    # Invalidate any previously set timer.
    if self.timer != None:
      self.timer.cancel()
      self.timer = None

  @staticmethod
  def on_post_save(view):
    view.run_command("solium_gutter")

class SoliumGutterStore:
  errors = []

  @classmethod
  def reset(self):
    self.errors = []
