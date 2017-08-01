########################################################################################################################
#  Begin CPH_Config.py Imports
########################################################################################################################

from logging import (
    DEBUG,
    ERROR,
    INFO,
    WARNING,
    getLevelName,
)
from collections import OrderedDict as odict, namedtuple
from difflib     import unified_diff
from itertools   import product
from json        import dump, dumps, load, loads
from thread      import start_new_thread
from webbrowser  import open_new_tab as browser_open

from burp import ITab
from CPH_Help import CPH_Help

from java.awt import (
    CardLayout,
    Color,
    FlowLayout,
    Font,
    GridBagConstraints,
    GridBagLayout,
    Insets,
)
from java.awt.event import (
    ActionListener,
    KeyListener,
    MouseAdapter,
)
from javax.swing import (
    AbstractAction,
    BorderFactory,
    JButton,
    JCheckBox,
    JComboBox,
    JFileChooser,
    JFrame,
    JLabel,
    JOptionPane,
    JPanel,
    JScrollPane,
    JSeparator,
    JSpinner,
    JSplitPane,
    JTabbedPane,
    JTable,
    JTextArea,
    JTextField,
    KeyStroke,
    SpinnerNumberModel,
)
from javax.swing.event import ChangeListener, ListSelectionListener
from javax.swing.table import AbstractTableModel
from javax.swing.undo import UndoManager
from javax.swing.filechooser import FileNameExtensionFilter

########################################################################################################################
#  End CPH_Config.py Imports
########################################################################################################################

########################################################################################################################
#  Begin CPH_Config.py
########################################################################################################################

class MainTab(ITab, ChangeListener):
    mainpane = JTabbedPane()

    def __init__(self, cph):
        MainTab.mainpane.addChangeListener(self)
        self._cph = cph
        self.options_tab = OptionsTab(cph)
        self.mainpane.add('Options', self.options_tab)
        self._add_sign = unichr(0x002b)  # addition sign
        self.mainpane.add(self._add_sign, JPanel())

        class Action(AbstractAction):
            def __init__(self, action):
                self.action = action
            def actionPerformed(self, e):
                if self.action:
                    self.action()
        # Ctrl+N only on key released
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(78, 2, True), 'add_config_tab')
        MainTab.mainpane.getActionMap().put('add_config_tab', Action(lambda: ConfigTab(self._cph)))
        # Ctrl+Shift+N only on key released
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(78, 3, True), 'clone_tab')
        MainTab.mainpane.getActionMap().put('clone_tab', Action(lambda: MainTab.mainpane.getSelectedComponent().clone_tab()
                                                                if MainTab.mainpane.getSelectedIndex() > 0
                                                                else None))
        # Ctrl+W only on key released
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(87, 2, True), 'close_tab')
        MainTab.mainpane.getActionMap().put('close_tab', Action(MainTab.close_tab))
        # Ctrl+E only on key released
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(69, 2, True), 'toggle_tab')
        MainTab.mainpane.getActionMap().put('toggle_tab', Action(lambda: MainTab.mainpane.getSelectedComponent().tabtitle_pane.enable_chkbox.setSelected(
            not MainTab.mainpane.getSelectedComponent().tabtitle_pane.enable_chkbox.isSelected())))
        # Ctrl+,
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(44, 2), 'select_previous_tab')
        MainTab.mainpane.getActionMap().put('select_previous_tab', Action(lambda: MainTab.mainpane.setSelectedIndex(MainTab.mainpane.getSelectedIndex() - 1)
                                                                          if MainTab.mainpane.getSelectedIndex() > 0
                                                                          else MainTab.mainpane.setSelectedIndex(0)))
        # Ctrl+.
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(46, 2), 'select_next_tab')
        MainTab.mainpane.getActionMap().put('select_next_tab', Action(lambda: MainTab.mainpane.setSelectedIndex(MainTab.mainpane.getSelectedIndex() + 1)))
        # Ctrl+Shift+,
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(44, 3), 'move_tab_back')
        MainTab.mainpane.getActionMap().put('move_tab_back', Action(lambda: MainTab.mainpane.getSelectedComponent().move_tab_back(
            MainTab.mainpane.getSelectedComponent())))
        # Ctrl+Shift+.
        MainTab.mainpane.getInputMap(1).put(KeyStroke.getKeyStroke(46, 3), 'move_tab_fwd')
        MainTab.mainpane.getActionMap().put('move_tab_fwd', Action(lambda: MainTab.mainpane.getSelectedComponent().move_tab_fwd(
            MainTab.mainpane.getSelectedComponent())))

    @staticmethod
    def getTabCaption():
        return 'CPH Config'

    @staticmethod
    def getOptionsTab():
        return MainTab.mainpane.getComponentAt(0)

    def getUiComponent(self):
        return self.mainpane

    def add_config_tab(self, messages):
        for message in messages:
            ConfigTab(self._cph, message)

    @staticmethod
    def get_config_tabs():
        components = MainTab.mainpane.getComponents()
        for i in range(len(components)):
            for tab in components:
                if isinstance(tab, ConfigTab) and i == MainTab.mainpane.indexOfComponent(tab):
                    yield tab

    @staticmethod
    def get_config_tab_names():
        for tab in MainTab.get_config_tabs():
            yield tab.namepane_txtfield.getText()

    @staticmethod
    def get_config_tab_cache(tab_name):
        for tab in MainTab.get_config_tabs():
            if tab.namepane_txtfield.getText() == tab_name:
                return tab.cached_request, tab.cached_response

    @staticmethod
    def check_configtab_names():
        x = 0
        configtab_names = {}
        for name in MainTab.get_config_tab_names():
            configtab_names[x] = name
            x += 1
        indices_to_rename = {}
        for tab_index_1, tab_name_1 in configtab_names.items():
            for tab_index_2, tab_name_2 in configtab_names.items():
                if tab_name_2 not in indices_to_rename:
                    indices_to_rename[tab_name_2] = []
                if tab_name_1 == tab_name_2 and tab_index_1 != tab_index_2:
                    indices_to_rename[tab_name_2].append(tab_index_2 + 1) # +1 because the first tab is the Options tab
        for k, v in indices_to_rename.items():
            indices_to_rename[k] = set(sorted(v))
        for tab_name, indices in indices_to_rename.items():
            x = 1
            for i in indices:
                MainTab.set_tab_name(MainTab.mainpane.getComponentAt(i), tab_name + ' (%s)' % x)
                x += 1

    @staticmethod
    def set_tab_name(tab, tab_name):
        tab.namepane_txtfield.tab_label.setText(tab_name)
        tab.namepane_txtfield.setText(tab_name)
        emv_tab_index = MainTab.mainpane.indexOfComponent(tab) - 1
        MainTab.getOptionsTab().emv_tab_pane.setTitleAt(emv_tab_index, tab_name)

    @staticmethod
    def close_tab(tabindex=None):
        if not tabindex:
            tabindex = MainTab.mainpane.getSelectedIndex()
        tabcount = MainTab.mainpane.getTabCount()
        if tabindex == 0 or tabcount == 2:
            return
        if tabcount == 3 or tabindex == tabcount - 2:
            MainTab.mainpane.setSelectedIndex(tabcount - 3)
        MainTab.mainpane.remove(tabindex)
        MainTab.getOptionsTab().emv_tab_pane.remove(tabindex - 1)
        ConfigTab.disable_all_cache_viewers()

    def stateChanged(self, e):
        if e.getSource() == self.mainpane:
            index = self.mainpane.getSelectedIndex()
            if hasattr(self, '_add_sign') and self.mainpane.getTitleAt(index) == self._add_sign:
                self.mainpane.setSelectedIndex(0)
                ConfigTab(self._cph)


class SubTab(JScrollPane, ActionListener):
    BTN_HELP = '?'
    DOCS_URL = 'https://elespike.github.io/burp-cph/'
    INSETS   = Insets(2, 4, 2, 4)

    def __init__(self, cph):
        self._cph = cph
        self._main_tab_pane = JPanel(GridBagLayout())
        self.setViewportView(self._main_tab_pane)
        self.getVerticalScrollBar().setUnitIncrement(16)

    @staticmethod
    def create_blank_space():
        return JLabel(' ')

    @staticmethod
    def create_empty_button(button):
        button.setOpaque(False)
        button.setFocusable(False)
        button.setContentAreaFilled(False)
        button.setBorderPainted(False)

    @staticmethod
    def set_title_font(component):
        font = Font(Font.SANS_SERIF, Font.BOLD, 14)
        component.setFont(font)
        return component

    def initialize_constraints(self):
        constraints = GridBagConstraints()
        constraints.weightx = 1
        constraints.insets = self.INSETS
        constraints.fill = GridBagConstraints.HORIZONTAL
        constraints.anchor = GridBagConstraints.NORTHWEST
        constraints.gridx = 0
        constraints.gridy = 0
        return constraints

    @staticmethod
    def get_exp_pane_values(pane):
        """
        See create_expression_pane() for details
        """
        comp_count = pane.getComponentCount()
        if comp_count == 1:
            # then there's no label and child_pane is the only component
            child_pane = pane.getComponent(0)
        elif comp_count == 2:
            # then there is a label and child_pane is the second component
            child_pane = pane.getComponent(1)
        return child_pane.getComponent(0).getText(), child_pane.getComponent(1).isSelected()

    @staticmethod
    def set_exp_pane_values(pane, text, check):
        """
        See create_expression_pane() for details
        """
        comp_count = pane.getComponentCount()
        if comp_count == 1:
            # then there's no label and child_pane is the only component
            child_pane = pane.getComponent(0)
        elif comp_count == 2:
            # then there is a label and child_pane is the second component
            child_pane = pane.getComponent(1)
        child_pane.getComponent(0).setText(text)
        child_pane.getComponent(1).setSelected(check)

    @staticmethod
    def show_card(cardpanel, label):
        cl = cardpanel.getLayout()
        cl.show(cardpanel, label)

    class HelpButton(JButton):
        def __init__(self, title, message, link=''):
            super(JButton, self).__init__()
            self.title   = title
            self.message = JLabel(message)
            self.message.setFont(Font(Font.MONOSPACED, Font.PLAIN, 14))

            self.link = SubTab.DOCS_URL
            if link:
                self.link = link

            self.setText(SubTab.BTN_HELP)
            self.setFont(Font(Font.SANS_SERIF, Font.BOLD, 14))

        def show_help(self):
            result = JOptionPane.showOptionDialog(
                self,
                self.message,
                self.title,
                JOptionPane.YES_NO_OPTION,
                JOptionPane.QUESTION_MESSAGE,
                None,
                ['Learn more', 'Close'],
                'Close'
            )
            if result == 0:
                browser_open(self.link)


class OptionsTab(SubTab, ChangeListener):
    BTN_DOCS = 'View full guide'
    BTN_EMV = 'Show EMV'
    BTN_QUICKSAVE = 'Quicksave'
    BTN_QUICKLOAD = 'Quickload'
    BTN_EXPORTCONFIG = 'Export Config'
    BTN_IMPORTCONFIG = 'Import Config'
    CHKBOX_PANE = 'Tool scope settings'
    VERBOSITY = 'Verbosity level:'
    QUICKSTART_PANE = 'Quickstart guide'

    configname_quick = 'quick'
    configname_enabled = 'enabled'
    configname_modify_type_choice_index = 'modify_type_choice_index'
    configname_modify_scope_choice_index = 'modify_scope_choice_index'
    configname_modify_exp = 'modify_exp'
    configname_modify_exp_regex = 'modify_exp_regex'
    configname_action_choice_index = 'action_choice_index'
    configname_indices_choice_index = 'indices_choice_index'
    configname_match_indices = 'match_indices'
    configname_auto_encode = 'auto_encode'
    configname_match_value = 'match_value'
    configname_match_value_regex = 'match_value_regex'
    configname_extract_choice_index = 'extract_choice_index'
    configname_static_value = 'static_value'
    configname_cached_value = 'cached_value'
    configname_cached_regex = 'cached_regex'
    configname_single_value = 'single_value'
    configname_single_regex = 'single_regex'
    configname_https = 'https'
    configname_update_cookies = 'update_cookies'
    configname_single_request = 'single_request'
    configname_single_response = 'single_response'
    configname_macro_value = 'macro_value'
    configname_macro_regex = 'macro_regex'

    def __init__(self, cph):
        SubTab.__init__(self, cph)
        self.loaded_config = odict()

        self.filefilter = FileNameExtensionFilter('JSON', ['json'])

        btn_docs = JButton(self.BTN_DOCS)
        btn_docs.addActionListener(self)
        btn_emv = JButton(self.BTN_EMV)
        btn_emv.addActionListener(self)
        btn_quicksave = JButton(self.BTN_QUICKSAVE)
        btn_quicksave.addActionListener(self)
        btn_quickload = JButton(self.BTN_QUICKLOAD)
        btn_quickload.addActionListener(self)
        btn_exportconfig = JButton(self.BTN_EXPORTCONFIG)
        btn_exportconfig.addActionListener(self)
        btn_importconfig = JButton(self.BTN_IMPORTCONFIG)
        btn_importconfig.addActionListener(self)

        err, warn, info, dbg = 1, 2, 3, 4
        self.verbosity_translator = {
            err : ERROR  ,
            warn: WARNING,
            info: INFO   ,
            dbg : DEBUG  ,
        }
        self.verbosity_level_lbl = JLabel(getLevelName(INFO))
        self.verbosity_spinner = JSpinner(SpinnerNumberModel(info, err, dbg, 1))
        self.verbosity_spinner.addChangeListener(self)

        verbosity_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        verbosity_pane.add(JLabel(self.VERBOSITY))
        verbosity_pane.add(self.verbosity_spinner)
        verbosity_pane.add(self.verbosity_level_lbl)

        self.emv = JFrame('Effective Modification Viewer')
        self.emv_tab_pane = JTabbedPane()
        self.emv.add(self.emv_tab_pane)

        btn_pane = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        constraints.gridwidth = 2
        btn_pane.add(verbosity_pane, constraints)
        constraints.gridwidth = 1
        constraints.gridy = 1
        btn_pane.add(btn_quicksave, constraints)
        constraints.gridx = 1
        btn_pane.add(btn_exportconfig, constraints)
        constraints.gridy = 2
        constraints.gridx = 0
        btn_pane.add(btn_quickload, constraints)
        constraints.gridx = 1
        btn_pane.add(btn_importconfig, constraints)
        constraints.gridy = 3
        constraints.gridx = 0
        btn_pane.add(btn_docs, constraints)
        constraints.gridx = 1
        btn_pane.add(btn_emv, constraints)

        self.chkbox_proxy = JCheckBox('Proxy', True)
        self.chkbox_target = JCheckBox('Target', False)
        self.chkbox_spider = JCheckBox('Spider', False)
        self.chkbox_repeater = JCheckBox('Repeater', True)
        self.chkbox_sequencer = JCheckBox('Sequencer', False)
        self.chkbox_intruder = JCheckBox('Intruder', False)
        self.chkbox_scanner = JCheckBox('Scanner', False)
        self.chkbox_extender = JCheckBox('Extender', False)

        chkbox_pane = JPanel(GridBagLayout())
        chkbox_pane.setBorder(BorderFactory.createTitledBorder(self.CHKBOX_PANE))
        chkbox_pane.getBorder().setTitleFont(Font(Font.SANS_SERIF, Font.ITALIC, 16))
        constraints = self.initialize_constraints()
        chkbox_pane.add(self.chkbox_proxy, constraints)
        constraints.gridy = 1
        chkbox_pane.add(self.chkbox_target, constraints)
        constraints.gridy = 2
        chkbox_pane.add(self.chkbox_spider, constraints)
        constraints.gridy = 3
        chkbox_pane.add(self.chkbox_repeater, constraints)
        constraints.gridx = 1
        constraints.gridy = 0
        chkbox_pane.add(self.chkbox_sequencer, constraints)
        constraints.gridy = 1
        chkbox_pane.add(self.chkbox_intruder, constraints)
        constraints.gridy = 2
        chkbox_pane.add(self.chkbox_scanner, constraints)
        constraints.gridy = 3
        chkbox_pane.add(self.chkbox_extender, constraints)

        quickstart_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        quickstart_pane.setBorder(BorderFactory.createTitledBorder(self.QUICKSTART_PANE))
        quickstart_pane.getBorder().setTitleFont(Font(Font.SANS_SERIF, Font.ITALIC, 16))
        quickstart_text_lbl = JLabel(CPH_Help.quickstart)
        quickstart_text_lbl.setFont(Font(Font.MONOSPACED, Font.PLAIN, 14))
        quickstart_pane.add(quickstart_text_lbl)

        constraints = self.initialize_constraints()
        constraints.gridwidth = 3
        self._main_tab_pane.add(self.create_blank_space(), constraints)
        constraints.gridwidth = 1
        constraints.gridy = 1
        self._main_tab_pane.add(btn_pane, constraints)
        constraints.gridx = 1
        self._main_tab_pane.add(self.create_blank_space(), constraints)
        constraints.gridx = 2
        self._main_tab_pane.add(chkbox_pane, constraints)
        constraints.gridx = 3
        self._main_tab_pane.add(self.create_blank_space(), constraints)
        constraints.gridx = 0
        constraints.gridy = 2
        constraints.gridwidth = 3
        self._main_tab_pane.add(self.create_blank_space(), constraints)
        constraints.gridy = 3
        constraints.weighty = 1
        self._main_tab_pane.add(quickstart_pane, constraints)

    def stateChanged(self, e):
        if e.getSource() == self.verbosity_spinner:
            level = self.verbosity_translator[self.verbosity_spinner.getValue()]
            self._cph.logger.setLevel(level)
            self.verbosity_level_lbl.setText(getLevelName(level))

    def set_tab_values(self, tab, tab_name, config):
        # Scope pane
        MainTab.set_tab_name(tab, tab_name)
        tab.tabtitle_pane.enable_chkbox.setSelected(
            config[self.configname_enabled])
        tab.msg_mod_combo_scope.setSelectedIndex(
            config[self.configname_modify_scope_choice_index])
        tab.msg_mod_combo_type.setSelectedIndex(
            config[self.configname_modify_type_choice_index])
        self.set_exp_pane_values(tab.msg_mod_exp_pane_scope,
                                 config[self.configname_modify_exp],
                                 config[self.configname_modify_exp_regex])
        tab.param_handl_combo_action.setSelectedIndex(
            config[self.configname_action_choice_index])
        tab.param_handl_combo_indices.setSelectedIndex(
            config[self.configname_indices_choice_index])
        tab.param_handl_txtfield_match_indices.setText(
            config[self.configname_match_indices])

        # Handling pane
        tab.param_handl_auto_encode_chkbox.setSelected(
            config[self.configname_auto_encode])
        self.set_exp_pane_values(tab.param_handl_exp_pane_target,
                                 config[self.configname_match_value],
                                 config[self.configname_match_value_regex])
        tab.param_handl_combo_extract.setSelectedIndex(
            config[self.configname_extract_choice_index])
        tab.param_handl_txtfield_extract_static.setText(
            config[self.configname_static_value])
        self.set_exp_pane_values(tab.param_handl_exp_pane_extract_cached,
                                 config[self.configname_cached_value],
                                 config[self.configname_cached_regex])
        self.set_exp_pane_values(tab.param_handl_exp_pane_extract_single,
                                 config[self.configname_single_value],
                                 config[self.configname_single_regex])
        tab.param_handl_https_chkbox.setSelected(
            config[self.configname_https])
        tab.param_handl_update_cookies_chkbox.setSelected(
            config[self.configname_update_cookies])
        tab.param_handl_request_editor.setMessage(self._cph.helpers.stringToBytes(
            config[self.configname_single_request]), True)
        tab.param_handl_response_editor.setMessage(self._cph.helpers.stringToBytes(
            config[self.configname_single_response]), False)
        self.set_exp_pane_values(tab.param_handl_exp_pane_extract_macro,
                                 config[self.configname_macro_value],
                                 config[self.configname_macro_regex])

    def actionPerformed(self, e):
        c = e.getActionCommand()
        if c == self.BTN_QUICKLOAD or c == self.BTN_IMPORTCONFIG:
            replace_config_tabs = False
            result = 0
            tabcount = 0
            for tab in MainTab.get_config_tabs():
                tabcount += 1
                break
            if tabcount > 0:
                result = JOptionPane.showOptionDialog(
                    self,
                    'Would you like to Purge or Keep all existing tabs?',
                    'Existing Tabs Detected!',
                    JOptionPane.YES_NO_CANCEL_OPTION,
                    JOptionPane.QUESTION_MESSAGE,
                    None,
                    ['Purge', 'Keep', 'Cancel'],
                    'Cancel'
                )
            # If purge...
            if result == 0:
                replace_config_tabs = True
                self._cph.logger.info('Replacing configuration...')
            # If not cancel or close dialog...
            # note: result can still be 0 here; do not use 'elif'
            if result != 2 and result != -1:
                if result != 0:
                    self._cph.logger.info('Merging configuration...')
                if c == self.BTN_QUICKLOAD:
                    try:
                        self.loaded_config = loads(self._cph.callbacks.loadExtensionSetting(self.configname_quick), object_pairs_hook=odict)
                        self.load_config(replace_config_tabs)
                        self._cph.logger.info('Configuration quickloaded.')
                    except StandardError:
                        self._cph.logger.exception('Error during quickload.')
                if c == self.BTN_IMPORTCONFIG:
                    fc = JFileChooser()
                    fc.setFileFilter(self.filefilter)
                    result = fc.showOpenDialog(self)
                    if result == JFileChooser.APPROVE_OPTION:
                        fpath = fc.getSelectedFile().getPath()
                        try:
                            with open(fpath, 'r') as f:
                                self.loaded_config = load(f, object_pairs_hook=odict)
                            self.load_config(replace_config_tabs)
                            self._cph.logger.info('Configuration imported from "{}".'.format(fpath))
                        except StandardError:
                            self._cph.logger.exception('Error importing config from "{}".'.format(fpath))
                    if result == JFileChooser.CANCEL_OPTION:
                        self._cph.logger.info('User canceled configuration import from file.')
            else:
                self._cph.logger.info('User canceled quickload/import.')

        if c == self.BTN_QUICKSAVE:
            try:
                full_config = self.prepare_to_save_all()
                self._cph.callbacks.saveExtensionSetting(self.configname_quick, dumps(full_config))
                self._cph.logger.info('Configuration quicksaved.')
            except StandardError:
                self._cph.logger.exception('Error during quicksave.')

        if c == self.BTN_DOCS:
            browser_open(self.DOCS_URL)

        if c == self.BTN_EMV:
            if not self.emv.isVisible():
                self.emv.pack()
                self.emv.setSize(800, 600)
                self.emv.show()
            # Un-minimize
            self.emv.setState(JFrame.NORMAL)
            self.emv.toFront()
            for emv_tab in self.emv_tab_pane.getComponents():
                emv_tab.viewer.setDividerLocation(0.5)

        if c == self.BTN_EXPORTCONFIG:
            tabcount = 0
            for tab in MainTab.get_config_tabs():
                tabcount += 1
                break
            if tabcount > 0:
                fc = JFileChooser()
                fc.setFileFilter(self.filefilter)
                result = fc.showSaveDialog(self)
                if result == JFileChooser.APPROVE_OPTION:
                    fpath = fc.getSelectedFile().getPath()
                    if not fpath.endswith('.json'):
                        fpath += '.json'
                    full_config = self.prepare_to_save_all()
                    try:
                        with open(fpath, 'w') as f:
                            dump(full_config, f, indent=4, separators=(',', ': '))
                        self._cph.logger.info('Configuration exported to "{}".'.format(fpath))
                    except IOError:
                        self._cph.logger.exception('Error exporting config to "{}".'.format(fpath))
                if result == JFileChooser.CANCEL_OPTION:
                    self._cph.logger.info('User canceled configuration export to file.')

    def load_config(self, replace_config_tabs):
        loaded_tab_names = [name for name in self.loaded_config]
        tabs_to_remove = {}

        # Modify existing and mark for purge where applicable
        # Using list(loaded_tab_names) to create a copy, since the original list is being modified within the loop
        for tab_name, tab in product(list(loaded_tab_names), MainTab.get_config_tabs()):
            if tab_name == tab.namepane_txtfield.getText():
                self.set_tab_values(tab, tab_name, self.loaded_config[tab_name])
                if tab_name in loaded_tab_names:
                    loaded_tab_names.remove(tab_name)
                tabs_to_remove[tab] = False
            if tab not in tabs_to_remove:
                tabs_to_remove[tab] = True

        # Import and purge if applicable
        for tab, tab_marked in tabs_to_remove.items():
            if tab_marked and replace_config_tabs:
                MainTab.getOptionsTab().emv_tab_pane.remove(tab.emv_tab)
                MainTab.mainpane.remove(tab)
        for tab_name in loaded_tab_names:
            self.set_tab_values(ConfigTab(self._cph), tab_name, self.loaded_config[tab_name])

        ConfigTab.disable_all_cache_viewers()

    def prepare_to_save_all(self):
        MainTab.check_configtab_names()
        full_config = odict()
        for tab in MainTab.get_config_tabs():
            full_config[tab.namepane_txtfield.getText()] = self.prepare_to_save_tab(tab)
        return full_config

    def prepare_to_save_tab(self, tab):
        config = {}
        # Scope pane
        config[self.configname_enabled                  ] = tab.tabtitle_pane.enable_chkbox.isSelected()
        config[self.configname_modify_scope_choice_index] = tab.msg_mod_combo_scope.getSelectedIndex()
        config[self.configname_modify_type_choice_index ] = tab.msg_mod_combo_type.getSelectedIndex()
        config[self.configname_modify_exp               ] , \
        config[self.configname_modify_exp_regex         ] = self.get_exp_pane_values(tab.msg_mod_exp_pane_scope)

        # Handling pane
        config[self.configname_auto_encode         ] = tab.param_handl_auto_encode_chkbox.isSelected()
        config[self.configname_match_value         ] , \
        config[self.configname_match_value_regex   ] = self.get_exp_pane_values(tab.param_handl_exp_pane_target)
        config[self.configname_action_choice_index ] = tab.param_handl_combo_action.getSelectedIndex()
        config[self.configname_indices_choice_index] = tab.param_handl_combo_indices.getSelectedIndex()
        config[self.configname_match_indices       ] = tab.param_handl_txtfield_match_indices.getText()
        config[self.configname_extract_choice_index] = tab.param_handl_combo_extract.getSelectedIndex()
        config[self.configname_static_value        ] = tab.param_handl_txtfield_extract_static.getText()
        config[self.configname_single_value        ] , \
        config[self.configname_single_regex        ] = self.get_exp_pane_values(tab.param_handl_exp_pane_extract_single)
        config[self.configname_https               ] = tab.param_handl_https_chkbox.isSelected()
        config[self.configname_update_cookies      ] = tab.param_handl_update_cookies_chkbox.isSelected()
        config[self.configname_single_request      ] = self._cph.helpers.bytesToString(tab.param_handl_request_editor.getMessage())
        config[self.configname_single_response     ] = self._cph.helpers.bytesToString(tab.param_handl_response_editor.getMessage())
        config[self.configname_macro_value         ] , \
        config[self.configname_macro_regex         ] = self.get_exp_pane_values(tab.param_handl_exp_pane_extract_macro)
        config[self.configname_cached_value        ] , \
        config[self.configname_cached_regex        ] = self.get_exp_pane_values(tab.param_handl_exp_pane_extract_cached)
        return config

class EMVTab(JSplitPane, ListSelectionListener):
    MAX_ITEMS = 30
    def __init__(self, configtab):
        self.configtab = configtab

        self.table = JTable(self.EMVTableModel())
        self.table_model = self.table.getModel()
        sm = self.table.getSelectionModel()
        sm.setSelectionMode(0) # Single selection
        sm.addListSelectionListener(self)

        table_pane = JScrollPane()
        table_pane.setViewportView(self.table)
        table_pane.getVerticalScrollBar().setUnitIncrement(16)

        self.original_field = JTextArea()
        self.original_field.setEditable(False)

        original_pane = JScrollPane()
        original_pane.setViewportView(self.original_field)
        original_pane.getVerticalScrollBar().setUnitIncrement(16)

        self.modified_field = JTextArea()
        self.modified_field.setEditable(False)

        modified_pane = JScrollPane()
        modified_pane.setViewportView(self.modified_field)
        modified_pane.getVerticalScrollBar().setUnitIncrement(16)

        self.viewer = JSplitPane()
        self.viewer.setLeftComponent(original_pane)
        self.viewer.setRightComponent(modified_pane)

        self.diff_field = JTextArea()
        self.diff_field.setEditable(False)

        diff_pane = JScrollPane()
        diff_pane.setViewportView(self.diff_field)
        diff_pane.getVerticalScrollBar().setUnitIncrement(16)

        diffpane = JSplitPane(JSplitPane.VERTICAL_SPLIT)
        diffpane.setTopComponent(diff_pane)
        diffpane.setBottomComponent(self.viewer)
        diffpane.setDividerLocation(100)

        viewer_pane = JPanel(GridBagLayout())
        constraints = GridBagConstraints()
        constraints.weightx = 1
        constraints.weighty = 1
        constraints.fill = GridBagConstraints.BOTH
        constraints.anchor = GridBagConstraints.NORTH
        constraints.gridx = 0
        constraints.gridy = 0
        viewer_pane.add(diffpane, constraints)

        self.setOrientation(JSplitPane.VERTICAL_SPLIT)
        self.setTopComponent(table_pane)
        self.setBottomComponent(viewer_pane)
        self.setDividerLocation(100)

    def add_table_row(self, time, is_request, original_msg, modified_msg):
        if len(self.table_model.rows) == 0:
            self.viewer.setDividerLocation(0.5)

        message_type = 'Response'
        if is_request:
            message_type = 'Request'
        self.table_model.rows.insert(0, [str(time)[:-3], message_type, len(modified_msg) - len(original_msg)])
        self.table_model.messages.insert(0, self.table_model.MessagePair(original_msg, modified_msg))

        if len(self.table_model.rows) > self.MAX_ITEMS:
            self.table_model.rows.pop(-1)
        if len(self.table_model.messages) > self.MAX_ITEMS:
            self.table_model.messages.pop(-1)

        self.table_model.fireTableDataChanged()
        self.table.setRowSelectionInterval(0, 0)

    def valueChanged(self, e):
        index = self.table.getSelectedRow()
        original_msg = self.table_model.messages[index].original_msg
        modified_msg = self.table_model.messages[index].modified_msg
        diff = unified_diff(original_msg.splitlines(1), modified_msg.splitlines(1))
        text = ''
        for line in diff:
            if '---' in line or '+++' in line:
                continue
            text += line
            if not text.endswith('\n'):
                text += '\n'
        self.diff_field.setText(text)
        self.original_field.setText(original_msg)
        self.modified_field.setText(modified_msg)

    class EMVTableModel(AbstractTableModel):
        def __init__(self):
            super(EMVTab.EMVTableModel, self).__init__()
            self.MessagePair = namedtuple('MessagePair', 'original_msg, modified_msg')
            self.rows = []
            self.messages = []

        def getRowCount(self):
            return len(self.rows)

        def getColumnCount(self):
            return 3

        def getColumnName(self, columnIndex):
            if columnIndex == 0:
                return 'Time'
            if columnIndex == 1:
                return 'Type'
            if columnIndex == 2:
                return 'Length Difference'

        def getValueAt(self, rowIndex, columnIndex):
            return self.rows[rowIndex][columnIndex]

        def setValueAt(self, aValue, rowIndex, columnIndex):
            return

        def isCellEditable(self, rowIndex, columnIndex):
            return False

class ConfigTabTitle(JPanel):
    def __init__(self):
        self.setBorder(BorderFactory.createEmptyBorder(-4, -5, -5, -5))
        self.setOpaque(False)
        self.enable_chkbox = JCheckBox('', True)
        self.label = JLabel(ConfigTab.TAB_NEW_NAME)
        self.label.setBorder(BorderFactory.createEmptyBorder(0, 0, 0, 4))
        self.add(self.enable_chkbox)
        self.add(self.label)
        self.add(self.CloseButton())

    class CloseButton(JButton, ActionListener):
        def __init__(self):
            self.setText(unichr(0x00d7))  # multiplication sign
            self.setBorder(BorderFactory.createEmptyBorder(0, 4, 0, 2))
            SubTab.create_empty_button(self)
            self.addMouseListener(self.CloseButtonMouseListener())
            self.addActionListener(self)

        def actionPerformed(self, e):
            MainTab.close_tab(MainTab.mainpane.indexOfTabComponent(self.getParent()))

        class CloseButtonMouseListener(MouseAdapter):
            def mouseEntered(self, e):
                button = e.getComponent()
                button.setForeground(Color.red)

            def mouseExited(self, e):
                button = e.getComponent()
                button.setForeground(Color.black)

            def mouseReleased(self, e):
                pass

            def mousePressed(self, e):
                pass


class ConfigTabNameField(JTextField, KeyListener):
    def __init__(self, tab_label):
        self.setColumns(25)
        self.setText(ConfigTab.TAB_NEW_NAME)
        self.addKeyListener(self)
        self.tab_label = tab_label

        self.addKeyListener(UndoableKeyListener(self))

    def keyReleased(self, e):
        self.tab_label.setText(self.getText())
        emv_tab_index = MainTab.mainpane.getSelectedIndex() - 1
        MainTab.getOptionsTab().emv_tab_pane.setTitleAt(emv_tab_index, self.getText())

    def keyPressed(self, e):
        # Doing self._tab_label.setText() here is sub-optimal. Leave it above.
        pass

    def keyTyped(self, e):
        pass


class UndoableKeyListener(KeyListener):
    REDO = 89
    UNDO = 90
    CTRL = 2
    def __init__(self, target):
        self.undomgr = UndoManager()
        target.getDocument().addUndoableEditListener(self.undomgr)

    def keyReleased(self, e):
        pass

    def keyPressed(self, e):
        if e.getModifiers() == self.CTRL:
            if e.getKeyCode() == self.UNDO and self.undomgr.canUndo():
                self.undomgr.undo()
            if e.getKeyCode() == self.REDO and self.undomgr.canRedo():
                self.undomgr.redo()

    def keyTyped(self, e):
        pass


class ConfigTab(SubTab):
    TXT_FIELD_SIZE = 45
    REGEX          = 'RegEx'
    TAB_NEW_NAME   = 'Unconfigured'

    # Scope pane
    BTN_BACK                    = '<'
    BTN_FWD                     = '>'
    BTN_CLONETAB                = 'Clone'
    TAB_NAME                    = 'Friendly name:'
    MSG_MOD_GROUP               = 'Scoping'
    MSG_MOD_SCOPE_BURP          = ' Provided their URLs are within Burp Suite\'s scope,'
    MSG_MOD_TYPES_TO_MODIFY     = 'this tab will work'
    MSG_MOD_COMBO_SCOPE_ALL     = 'on all'
    MSG_MOD_COMBO_SCOPE_SOME    = 'only on'
    MSG_MOD_COMBO_SCOPE_CHOICES = [
        MSG_MOD_COMBO_SCOPE_ALL,
        MSG_MOD_COMBO_SCOPE_SOME,
    ]
    MSG_MOD_COMBO_TYPE_REQ     = 'requests'
    MSG_MOD_COMBO_TYPE_RESP    = 'responses'
    MSG_MOD_COMBO_TYPE_BOTH    = 'requests and responses'
    MSG_MOD_COMBO_TYPE_CHOICES = [
        MSG_MOD_COMBO_TYPE_REQ ,
        MSG_MOD_COMBO_TYPE_RESP,
        MSG_MOD_COMBO_TYPE_BOTH,
    ]
    MSG_MOD_SCOPE_SOME = ' containing this expression:'

    # Handling pane
    PARAM_HANDL_GROUP                 = 'Parameter handling'
    PARAM_HANDL_AUTO_ENCODE           = '<html>Automatically URL-encode the first line of the request, if modified<br>&nbsp;</html>'
    PARAM_HANDL_MATCH_EXP             = ' 1) Find matches to this expression:'
    PARAM_HANDL_TARGET                = '2) Target'
    PARAM_HANDL_COMBO_INDICES_FIRST   = 'the first'
    PARAM_HANDL_COMBO_INDICES_EACH    = 'each'
    PARAM_HANDL_COMBO_INDICES_SUBSET  = 'a subset'
    PARAM_HANDL_COMBO_INDICES_CHOICES = [
        PARAM_HANDL_COMBO_INDICES_FIRST ,
        PARAM_HANDL_COMBO_INDICES_EACH  ,
        PARAM_HANDL_COMBO_INDICES_SUBSET,
    ]
    PARAM_HANDL_MATCH_RANGE          = 'of the matches'
    PARAM_HANDL_MATCH_SUBSET         = 'Which subset?'
    PARAM_HANDL_ACTION_PREFIX        = '3)'
    PARAM_HANDL_COMBO_ACTION_REPLACE = 'Replace'
    PARAM_HANDL_COMBO_ACTION_INSERT  = 'Append to'
    PARAM_HANDL_COMBO_ACTION_CHOICES = [
        PARAM_HANDL_COMBO_ACTION_REPLACE,
        PARAM_HANDL_COMBO_ACTION_INSERT ,
    ]
    PARAM_HANDL_ACTION_SUFFIX         = 'each target {}the following:'
    PARAM_HANDL_COMBO_EXTRACT_STATIC  = 'a static value specified below'
    PARAM_HANDL_COMBO_EXTRACT_SINGLE  = 'a value returned by issuing a single request'
    PARAM_HANDL_COMBO_EXTRACT_MACRO   = 'a value returned by issuing a sequence of requests'
    PARAM_HANDL_COMBO_EXTRACT_CACHED  = 'a value in the cached response of a previous CPH tab'
    PARAM_HANDL_COMBO_EXTRACT_SCACHED = 'a value in the cached response of a previous CPH tab single request'
    PARAM_HANDL_COMBO_EXTRACT_CHOICES = [
        PARAM_HANDL_COMBO_EXTRACT_STATIC ,
        PARAM_HANDL_COMBO_EXTRACT_SINGLE ,
        PARAM_HANDL_COMBO_EXTRACT_MACRO  ,
        PARAM_HANDL_COMBO_EXTRACT_CACHED ,
        PARAM_HANDL_COMBO_EXTRACT_SCACHED,
    ]
    PARAM_HANDL_EXTRACT_STATIC      = 'Please note: line separators in this multiline field will be converted to 0x0d0a in the resulting HTTP request'
    PARAM_HANDL_UPDATE_COOKIES      = 'Update cookies'
    PARAM_HANDL_HTTPS               = 'Issue over HTTPS'
    PARAM_HANDL_BTN_ISSUE           = 'Issue'
    PARAM_HANDL_EXTRACT_SINGLE      = 'the request in the left pane, then extract the value from its response with this expression:'
    PARAM_HANDL_EXTRACT_MACRO       = 'When invoked from a Session Handling Rule, CPH will extract the value from the final macro response with this expression:'
    PARAM_HANDL_EXTRACT_CACHED_PRE  = 'Extract the value from'
    PARAM_HANDL_EXTRACT_CACHED_POST = '\'s cached response with this expression:'

    def __init__(self, cph, message=None):
        SubTab.__init__(self, cph)
        self.request, self.response = self.initialize_req_resp()
        self.cached_request, self.cached_response = self.initialize_req_resp()
        if message:
            self.request = message.getRequest()
            resp = message.getResponse()
            if resp:
                self.response = resp
        self.cached_match = ''

        index = MainTab.mainpane.getTabCount() - 1
        MainTab.mainpane.add(self, index)
        self.tabtitle_pane = ConfigTabTitle()
        MainTab.mainpane.setTabComponentAt(index, self.tabtitle_pane)
        MainTab.mainpane.setSelectedIndex(index)

        btn_back = self.set_title_font(JButton(self.BTN_BACK))
        btn_back.addActionListener(self)
        btn_fwd = self.set_title_font(JButton(self.BTN_FWD))
        btn_fwd.addActionListener(self)
        btn_clonetab = JButton(self.BTN_CLONETAB)
        btn_clonetab.addActionListener(self)
        controlpane = JPanel(FlowLayout(FlowLayout.LEADING))
        controlpane.add(btn_back)
        controlpane.add(btn_fwd)
        controlpane.add(self.create_blank_space())
        controlpane.add(btn_clonetab)

        namepane = JPanel(FlowLayout(FlowLayout.LEADING))
        namepane.add(self.set_title_font(JLabel(self.TAB_NAME)))
        self.namepane_txtfield = ConfigTabNameField(self.tabtitle_pane.label)
        namepane.add(self.namepane_txtfield)

        msg_mod_layout_pane = JPanel(GridBagLayout())
        msg_mod_layout_pane.setBorder(BorderFactory.createTitledBorder(self.MSG_MOD_GROUP))
        msg_mod_layout_pane.getBorder().setTitleFont(Font(Font.SANS_SERIF, Font.ITALIC, 16))

        param_handl_layout_pane = JPanel(GridBagLayout())
        param_handl_layout_pane.setBorder(BorderFactory.createTitledBorder(self.PARAM_HANDL_GROUP))
        param_handl_layout_pane.getBorder().setTitleFont(Font(Font.SANS_SERIF, Font.ITALIC, 16))

        self.msg_mod_combo_scope = JComboBox(self.MSG_MOD_COMBO_SCOPE_CHOICES)
        self.msg_mod_combo_scope.addActionListener(self)
        self.msg_mod_combo_type = JComboBox(self.MSG_MOD_COMBO_TYPE_CHOICES)
        self.msg_mod_combo_type.addActionListener(self)
        self.msg_mod_exp_pane_scope_lbl = JLabel(self.MSG_MOD_SCOPE_SOME)
        self.msg_mod_exp_pane_scope_lbl.setVisible(False)
        self.msg_mod_exp_pane_scope = self.create_expression_pane()
        self.msg_mod_exp_pane_scope.setVisible(False)

        self.param_handl_exp_pane_target = self.create_expression_pane()
        self.param_handl_auto_encode_chkbox = JCheckBox(self.PARAM_HANDL_AUTO_ENCODE, True)
        self.param_handl_auto_encode_chkbox.setVerticalTextPosition(1) # 1 is Top
        self.param_handl_combo_indices = JComboBox(self.PARAM_HANDL_COMBO_INDICES_CHOICES)
        self.param_handl_combo_indices.addActionListener(self)
        self.param_handl_combo_action = JComboBox(self.PARAM_HANDL_COMBO_ACTION_CHOICES)
        self.param_handl_combo_action.addActionListener(self)
        self.param_handl_txtfield_match_indices = JTextField(12)
        self.param_handl_txtfield_match_indices.addKeyListener(
            UndoableKeyListener(self.param_handl_txtfield_match_indices))
        self.param_handl_txtfield_match_indices.setText('0')
        self.param_handl_txtfield_match_indices.setEnabled(False)
        self.param_handl_button_indices_help = self.HelpButton(CPH_Help.indices.title, CPH_Help.indices.message, SubTab.DOCS_URL + '#quickstart/indices')
        self.param_handl_button_indices_help.addActionListener(self)
        self.param_handl_action_lbl = self.set_title_font(JLabel(self.PARAM_HANDL_ACTION_SUFFIX.format('with ')))
        self.param_handl_subset_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        self.param_handl_exp_pane_extract_cached = self.create_expression_pane(enforce_regex=True)
        self.param_handl_exp_pane_extract_single = self.create_expression_pane(enforce_regex=True)
        self.param_handl_exp_pane_extract_macro = self.create_expression_pane(enforce_regex=True, label=self.PARAM_HANDL_EXTRACT_MACRO)
        self.param_handl_txtfield_extract_static = JTextArea()
        self.param_handl_txtfield_extract_static.setLineWrap(True)
        self.param_handl_txtfield_extract_static.setColumns(self.TXT_FIELD_SIZE)
        self.param_handl_txtfield_extract_static.addKeyListener(
            UndoableKeyListener(self.param_handl_txtfield_extract_static))
        self.param_handl_cached_req_viewer = self._cph.callbacks.createMessageEditor(None, False)
        self.param_handl_cached_req_viewer.setMessage(self.cached_request, True)
        self.param_handl_cached_resp_viewer = self._cph.callbacks.createMessageEditor(None, False)
        self.param_handl_cached_resp_viewer.setMessage(self.cached_response, False)
        self.param_handl_https_chkbox = JCheckBox(self.PARAM_HANDL_HTTPS)
        self.param_handl_update_cookies_chkbox = JCheckBox(self.PARAM_HANDL_UPDATE_COOKIES, True)
        self.param_handl_request_editor = self._cph.callbacks.createMessageEditor(None, True)
        self.param_handl_request_editor.setMessage(self.request, True)
        self.param_handl_response_editor = self._cph.callbacks.createMessageEditor(None, False)
        self.param_handl_response_editor.setMessage(self.response, False)
        self.param_handl_cardpanel_static_or_extract = JPanel(FlexibleCardLayout())
        self.param_handl_combo_extract = JComboBox(self.PARAM_HANDL_COMBO_EXTRACT_CHOICES)
        self.param_handl_combo_extract.addActionListener(self)
        self.param_handl_button_extract_static_help = self.HelpButton(CPH_Help.extract_static.title, CPH_Help.extract_static.message, SubTab.DOCS_URL + '#quickstart/find_replace')
        self.param_handl_button_extract_single_help = self.HelpButton(CPH_Help.extract_single.title, CPH_Help.extract_single.message, SubTab.DOCS_URL + '#quickstart/extract_single')
        self.param_handl_button_extract_macro_help = self.HelpButton(CPH_Help.extract_macro.title, CPH_Help.extract_macro.message, SubTab.DOCS_URL + '#quickstart/extract_macro')
        self.param_handl_button_extract_cached_help = self.HelpButton(CPH_Help.extract_cached.title, CPH_Help.extract_cached.message, SubTab.DOCS_URL + '#quickstart/extract_cached')
        self.param_handl_combo_cached = JComboBox()
        self.param_handl_combo_cached.addActionListener(self)

        self.build_msg_mod_pane(msg_mod_layout_pane)
        self.build_param_handl_pane(param_handl_layout_pane)

        if self.request:
            self.param_handl_combo_extract.setSelectedItem(self.PARAM_HANDL_COMBO_EXTRACT_SINGLE)

        constraints = self.initialize_constraints()
        constraints.weighty = 0.05
        self._main_tab_pane.add(controlpane, constraints)
        constraints.gridy = 1
        self._main_tab_pane.add(namepane, constraints)
        constraints.gridy = 2
        self._main_tab_pane.add(msg_mod_layout_pane, constraints)
        constraints.gridy = 3
        constraints.weighty = 1
        self._main_tab_pane.add(param_handl_layout_pane, constraints)

        self.emv_tab = EMVTab(self)
        MainTab.getOptionsTab().emv_tab_pane.add(self.namepane_txtfield.getText(), self.emv_tab)

    def initialize_req_resp(self):
        return [], self._cph.helpers.stringToBytes(''.join([' \r\n' for i in range(6)]))

    def create_expression_pane(self, enforce_regex=False, label=None):
        field = JTextField()
        field.setColumns(self.TXT_FIELD_SIZE)

        field.addKeyListener(UndoableKeyListener(field))

        box = JCheckBox(self.REGEX)
        if enforce_regex:
            box.setEnabled(False)
            box.setSelected(True)

        child_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        child_pane.add(field)
        child_pane.add(box)

        parent_pane = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        if label:
            parent_pane.add(JLabel(label), constraints)
            constraints.gridy += 1
        parent_pane.add(child_pane, constraints)

        return parent_pane

    def build_msg_mod_pane(self, msg_mod_pane):
        msg_mod_req_or_resp_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        msg_mod_req_or_resp_pane.add(JLabel(self.MSG_MOD_TYPES_TO_MODIFY))
        msg_mod_req_or_resp_pane.add(self.msg_mod_combo_scope)
        msg_mod_req_or_resp_pane.add(self.msg_mod_combo_type)
        msg_mod_req_or_resp_pane.add(self.msg_mod_exp_pane_scope_lbl)

        constraints = self.initialize_constraints()
        msg_mod_pane.add(self.set_title_font(JLabel(self.MSG_MOD_SCOPE_BURP)), constraints)
        constraints.gridy = 1
        msg_mod_pane.add(msg_mod_req_or_resp_pane, constraints)
        constraints.gridy = 2
        msg_mod_pane.add(self.msg_mod_exp_pane_scope, constraints)

    def build_param_handl_pane(self, param_derivation_pane):
        target_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        target_pane.add(self.set_title_font(JLabel(self.PARAM_HANDL_TARGET)))
        target_pane.add(self.param_handl_combo_indices)
        target_pane.add(self.set_title_font(JLabel(self.PARAM_HANDL_MATCH_RANGE)))

        self.param_handl_subset_pane.add(JLabel(self.PARAM_HANDL_MATCH_SUBSET))
        self.param_handl_subset_pane.add(self.param_handl_txtfield_match_indices)
        self.param_handl_subset_pane.add(self.param_handl_button_indices_help)
        self.param_handl_subset_pane.setVisible(False)

        action_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        action_pane.add(self.set_title_font(JLabel(self.PARAM_HANDL_ACTION_PREFIX)))
        action_pane.add(self.param_handl_combo_action)
        action_pane.add(self.param_handl_action_lbl)

        static_param_card = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        constraints.fill = GridBagConstraints.NONE
        static_param_card.add(self.param_handl_txtfield_extract_static, constraints)
        constraints.gridy = 1
        static_param_card.add(JLabel(self.PARAM_HANDL_EXTRACT_STATIC), constraints)

        derive_param_single_card = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        chkbox_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        chkbox_pane.add(self.param_handl_update_cookies_chkbox)
        chkbox_pane.add(self.param_handl_https_chkbox)
        derive_param_single_card.add(chkbox_pane, constraints)
        constraints.gridy = 1
        issue_request_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        issue_request_button = JButton(self.PARAM_HANDL_BTN_ISSUE)
        issue_request_button.addActionListener(self)
        issue_request_pane.add(issue_request_button)
        issue_request_pane.add(JLabel(self.PARAM_HANDL_EXTRACT_SINGLE))
        derive_param_single_card.add(issue_request_pane, constraints)
        constraints.gridy = 2
        derive_param_single_card.add(self.param_handl_exp_pane_extract_single, constraints)
        constraints.gridy = 3
        constraints.gridwidth = 2
        splitpane = JSplitPane()
        splitpane.setLeftComponent(self.param_handl_request_editor.getComponent())
        splitpane.setRightComponent(self.param_handl_response_editor.getComponent())
        derive_param_single_card.add(splitpane, constraints)
        splitpane.setDividerLocation(0.5)

        derive_param_macro_card = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        derive_param_macro_card.add(self.param_handl_exp_pane_extract_macro, constraints)

        cached_param_card = JPanel(GridBagLayout())
        constraints = self.initialize_constraints()
        tab_choice_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        tab_choice_pane.add(JLabel(self.PARAM_HANDL_EXTRACT_CACHED_PRE))
        tab_choice_pane.add(self.param_handl_combo_cached)
        tab_choice_pane.add(JLabel(self.PARAM_HANDL_EXTRACT_CACHED_POST))
        cached_param_card.add(tab_choice_pane, constraints)
        constraints.gridy = 1
        cached_param_card.add(self.param_handl_exp_pane_extract_cached, constraints)
        constraints.gridy = 2
        constraints.gridwidth = 2
        splitpane = JSplitPane()
        splitpane.setLeftComponent(self.param_handl_cached_req_viewer.getComponent())
        splitpane.setRightComponent(self.param_handl_cached_resp_viewer.getComponent())
        cached_param_card.add(splitpane, constraints)
        splitpane.setDividerLocation(0.5)

        self.param_handl_cardpanel_static_or_extract.add(static_param_card, self.PARAM_HANDL_COMBO_EXTRACT_STATIC)
        self.param_handl_cardpanel_static_or_extract.add(derive_param_single_card, self.PARAM_HANDL_COMBO_EXTRACT_SINGLE)
        self.param_handl_cardpanel_static_or_extract.add(derive_param_macro_card, self.PARAM_HANDL_COMBO_EXTRACT_MACRO)
        self.param_handl_cardpanel_static_or_extract.add(cached_param_card, self.PARAM_HANDL_COMBO_EXTRACT_CACHED)

        constraints = self.initialize_constraints()
        param_derivation_pane.add(self.param_handl_auto_encode_chkbox, constraints)
        constraints.gridy = 1
        param_derivation_pane.add(self.set_title_font(JLabel(self.PARAM_HANDL_MATCH_EXP)), constraints)
        constraints.gridy = 2
        param_derivation_pane.add(self.param_handl_exp_pane_target, constraints)
        constraints.gridy = 3
        param_derivation_pane.add(target_pane, constraints)
        constraints.gridy = 4
        param_derivation_pane.add(self.param_handl_subset_pane, constraints)
        constraints.gridy = 5
        param_derivation_pane.add(action_pane, constraints)
        constraints.gridy = 6
        # Making a FlowLayout panel here so the combo box doesn't stretch
        combo_pane = JPanel(FlowLayout(FlowLayout.LEADING))
        combo_pane.add(self.param_handl_combo_extract)
        placeholder_btn = self.HelpButton('', '')
        placeholder_btn.addActionListener(self)
        combo_pane.add(placeholder_btn)
        combo_pane.add(self.create_blank_space())
        param_derivation_pane.add(combo_pane, constraints)
        constraints.gridy = 7
        constraints.gridwidth = GridBagConstraints.REMAINDER - 1
        param_derivation_pane.add(self.param_handl_cardpanel_static_or_extract, constraints)

    @staticmethod
    def move_tab(tab, desired_index):
        if desired_index <= 0 or desired_index >= MainTab.mainpane.getTabCount() - 1:
            return

        MainTab.mainpane.setSelectedIndex(0)
        emv_sel_tab = MainTab.getOptionsTab().emv_tab_pane.getSelectedComponent()
        current_index = MainTab.mainpane.indexOfComponent(tab)
        if current_index > desired_index:
            MainTab.mainpane.add(tab, desired_index)
            MainTab.getOptionsTab().emv_tab_pane.add(tab.emv_tab, desired_index - 1)
        else:
            # I've no idea why +1 is needed here. =)
            MainTab.mainpane.add(tab, desired_index + 1)
            MainTab.getOptionsTab().emv_tab_pane.add(tab.emv_tab, desired_index)

        MainTab.mainpane.setTabComponentAt(desired_index, tab.tabtitle_pane)
        MainTab.mainpane.setSelectedIndex(desired_index)
        MainTab.getOptionsTab().emv_tab_pane.setTitleAt(desired_index - 1, tab.namepane_txtfield.getText())
        MainTab.getOptionsTab().emv_tab_pane.setSelectedComponent(emv_sel_tab)

    @staticmethod
    def move_tab_back(tab):
        desired_index = MainTab.mainpane.getSelectedIndex() - 1
        ConfigTab.move_tab(tab, desired_index)

    @staticmethod
    def move_tab_fwd(tab):
        desired_index = MainTab.mainpane.getSelectedIndex() + 1
        ConfigTab.move_tab(tab, desired_index)

    def clone_tab(self):
        desired_index = MainTab.mainpane.getSelectedIndex() + 1

        newtab = ConfigTab(self._cph)
        MainTab.set_tab_name(newtab, self.namepane_txtfield.getText())
        config = MainTab.getOptionsTab().prepare_to_save_tab(self)
        MainTab.getOptionsTab().loaded_config = {self.namepane_txtfield.getText(): config}
        MainTab.getOptionsTab().load_config(False)

        ConfigTab.move_tab(newtab, desired_index)
        MainTab.check_configtab_names()

    def disable_cache_viewers(self):
        self.cached_request, self.cached_response = self.initialize_req_resp()
        self.param_handl_cached_req_viewer.setMessage(self.cached_request, False)
        self.param_handl_cached_resp_viewer.setMessage(self.cached_response, False)

    @staticmethod
    def disable_all_cache_viewers():
        for tab in MainTab.mainpane.getComponents():
            if isinstance(tab, ConfigTab):
                tab.disable_cache_viewers()

    def actionPerformed(self, e):
        c = e.getActionCommand()
        self._cph.logger.debug('Firing action command: {}'.format(c))

        if c == self.BTN_HELP:
            source = e.getSource()
            if source.title:
                source.show_help()
            else:
                # The dynamic help button (placeholder_btn) has no title, so here we're using it
                # to show the appropriate help message based on the selected combobox item.
                extract_combo_selection = self.param_handl_combo_extract.getSelectedItem()
                if extract_combo_selection == self.PARAM_HANDL_COMBO_EXTRACT_STATIC:
                    self.param_handl_button_extract_static_help.show_help()
                if extract_combo_selection == self.PARAM_HANDL_COMBO_EXTRACT_SINGLE:
                    self.param_handl_button_extract_single_help.show_help()
                if extract_combo_selection == self.PARAM_HANDL_COMBO_EXTRACT_MACRO:
                    self.param_handl_button_extract_macro_help.show_help()
                if extract_combo_selection == self.PARAM_HANDL_COMBO_EXTRACT_CACHED:
                    self.param_handl_button_extract_cached_help.show_help()

        if c == 'comboBoxChanged':
            c = e.getSource().getSelectedItem()
            self._cph.logger.debug('Action command is now: {}'.format(c))

        if c == self.MSG_MOD_COMBO_TYPE_RESP:
            self.param_handl_auto_encode_chkbox.setVisible(False)
        elif c == self.MSG_MOD_COMBO_TYPE_REQ or c == self.MSG_MOD_COMBO_TYPE_BOTH:
            self.param_handl_auto_encode_chkbox.setVisible(True)

        if c == self.MSG_MOD_COMBO_SCOPE_ALL:
            self.msg_mod_exp_pane_scope_lbl.setVisible(False)
            self.msg_mod_exp_pane_scope.setVisible(False)
        if c == self.MSG_MOD_COMBO_SCOPE_SOME:
            self.msg_mod_exp_pane_scope_lbl.setVisible(True)
            self.msg_mod_exp_pane_scope.setVisible(True)

        if c == self.PARAM_HANDL_COMBO_ACTION_INSERT:
            self.param_handl_action_lbl.setText(self.PARAM_HANDL_ACTION_SUFFIX.format(''))
        if c == self.PARAM_HANDL_COMBO_ACTION_REPLACE:
            self.param_handl_action_lbl.setText(self.PARAM_HANDL_ACTION_SUFFIX.format('with '))

        if c == self.PARAM_HANDL_COMBO_INDICES_FIRST:
            self.param_handl_txtfield_match_indices.setEnabled(False)
            self.param_handl_txtfield_match_indices.setText('0')
            self.param_handl_subset_pane.setVisible(False)
        if c == self.PARAM_HANDL_COMBO_INDICES_EACH:
            self.param_handl_txtfield_match_indices.setEnabled(False)
            self.param_handl_txtfield_match_indices.setText('0:-1,-1')
            self.param_handl_subset_pane.setVisible(False)
        if c == self.PARAM_HANDL_COMBO_INDICES_SUBSET:
            self.param_handl_txtfield_match_indices.setEnabled(True)
            self.param_handl_subset_pane.setVisible(True)

        if c in self.PARAM_HANDL_COMBO_EXTRACT_CHOICES:
            self.show_card(self.param_handl_cardpanel_static_or_extract, c)

        # Set the cached request/response viewers to the selected tab's cache
        if c in MainTab.get_config_tab_names():
            req, resp = MainTab.get_config_tab_cache(c)
            if req and resp:
                self.param_handl_cached_req_viewer.setMessage(req, True)
                self.param_handl_cached_resp_viewer.setMessage(resp, False)

        if c == self.PARAM_HANDL_BTN_ISSUE:
            start_new_thread(self._cph.issue_request, (self,))

        if c == self.BTN_BACK:
            self.move_tab_back(self)
            self.disable_all_cache_viewers()
        if c == self.BTN_FWD:
            self.move_tab_fwd(self)
            self.disable_all_cache_viewers()

        if c == self.BTN_CLONETAB:
            self.clone_tab()
            self.disable_all_cache_viewers()


class FlexibleCardLayout(CardLayout):
    def __init__(self):
        super(FlexibleCardLayout, self).__init__()

    def preferredLayoutSize(self, parent):
        current = self.find_current_component(parent)
        if current:
            insets = parent.getInsets()
            pref = current.getPreferredSize()
            pref.width += insets.left + insets.right
            pref.height += insets.top + insets.bottom
            return pref
        return super.preferredLayoutSize(parent)

    @staticmethod
    def find_current_component(parent):
        for comp in parent.getComponents():
            if comp.isVisible():
                return comp
        return None

########################################################################################################################
#  End CPH_Config.py
########################################################################################################################

