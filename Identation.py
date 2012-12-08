import sublime, sublime_plugin, re


class Identation(sublime_plugin.EventListener):
    def __init__(self):
        sublime_plugin.EventListener.__init__(self)
        self.skip_modified = set()
        self.viewport_position = {}
        self.extensions = set(['hs', 'py', 'c', 'cc', 'cpp', 'java', 'js', 'html'])

    def our_view(func):
        def proxy(self, view):
            file_name = view.file_name()
            if file_name and file_name.split('.')[-1] in self.extensions:
                func(self, view)
        return proxy

    @our_view
    def on_load(self, view):
        edit_position = view.sel()[0]
        edit_region = sublime.Region(edit_position.a, edit_position.b)

        region = sublime.Region(0, view.size())
        data = view.substr(region)

        view.settings().set('translate_tabs_to_spaces', False)
        tab_size = view.settings().get('tab_size')

        patch = lambda line: re.sub('^(\ {%d})+' % tab_size,
            lambda match: '\t' * (len(match.group(0))/tab_size), line).rstrip()
        data = '\n'.join(map(patch, data.split('\n')))
        if not data.endswith('\n'):
            data = data + '\n'

        edit = view.begin_edit()
        view.replace(edit, region, data)
        view.end_edit(edit)

        cursor = view.sel()
        cursor.clear()
        cursor.add(edit_region)
        view.show(edit_region)

        view.set_scratch(True)
        self.skip_modified.add(view.id())

    @our_view
    def on_pre_save(self, view):
        self.viewport_position[view.id()] = view.viewport_position()
        view.run_command('expand_tabs') # {'set_translate_tabs':True}

    @our_view
    def on_post_save(self, view):
        view.run_command('unexpand_tabs')
        view.set_viewport_position(self.viewport_position.pop(view.id()), False)
        view.set_scratch(True)
        self.skip_modified.add(view.id())

    @our_view
    def on_modified(self, view):
        if view.id() in self.skip_modified:
            self.skip_modified.remove(view.id())
        else:
            view.set_scratch(False)
