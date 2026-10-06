import json
import os
import unittest
from helpers import Fixture, SOURCE


class ReadHooks(Fixture):
    def test_whole_file_boundary(self):
        for vendor in ['claude', 'codex', 'cursor']:
            with self.subTest(vendor=vendor):
                self.assert_gate('Read', {'file_path': str(self.small)}, False, vendor)
                self.assert_gate('Read', {'file_path': str(self.large)}, True, vendor)

    def test_read_window_boundary(self):
        for count, denied in [(100, False), (101, True), (150, True)]:
            with self.subTest(count=count):
                self.assert_gate('view_file', {'AbsolutePath': str(self.large), 'StartLine': 1, 'EndLine': count}, denied, 'antigravity')

    def test_offset_has_no_off_by_one(self):
        self.assert_gate('Read', {'file_path': str(self.large), 'offset': 1, 'limit': 100}, False)

    def test_invalid_ranges_deny_cleanly(self):
        for extra in [{'offset':'bad','limit':100}, {'offset':True,'limit':100},
                      {'StartLine':4,'EndLine':2}, {'view_range':[1]}, {'StartLine':1}]:
            with self.subTest(extra=extra):
                self.assert_gate('Read', {'file_path': str(self.large), **extra}, True)

    def test_native_cursor_before_read_payload(self):
        raw = json.dumps({'hook_event_name':'beforeReadFile', 'file_path':str(self.large),
                          'cwd':str(self.root), 'content':self.large.read_text()})
        denied, _, response = self.invoke('', {}, 'cursor', raw)
        self.assertTrue(denied)
        self.assertEqual(response['permission'], 'deny')

    def test_malformed_payloads_fail_closed(self):
        for raw in ['{invalid', '[]', '{}', '', '{"tool_name": "Edit", "tool_input": "bad"}']:
            with self.subTest(raw=raw):
                denied, result, _ = self.invoke('', {}, raw=raw)
                self.assertTrue(denied)
                self.assertEqual(result.returncode, 2)

    def test_section_tools_use_server_caps(self):
        self.assert_gate('mcp__markdown_docs__read_section', {'file_path':str(self.large), 'section_id':'s1'}, False)


class EditHooks(Fixture):
    def test_inside_edit_and_outside_denial(self):
        for vendor in ['claude', 'codex', 'cursor']:
            with self.subTest(vendor=vendor):
                self.assert_gate('Edit', {'file_path':str(self.main), 'old_string':'user_call();', 'new_string':'safe();'}, False, vendor)
                self.assert_gate('Edit', {'file_path':str(self.main), 'old_string':'int generated = 0;', 'new_string':'int generated = 1;'}, True, vendor)

    def test_replace_all_checks_every_occurrence(self):
        self.assert_gate('Edit', {'file_path':str(self.main), 'old_string':'shared();', 'new_string':'unsafe();', 'replace_all':True}, True)

    def test_ambiguous_edit_needs_context(self):
        self.assert_gate('Edit', {'file_path':str(self.main), 'old_string':'shared();', 'new_string':'safe();'}, True)

    def test_markers_cannot_be_deleted_or_injected(self):
        pairs = [('/* USER CODE BEGIN 0 */',''),
                 ('user_call();','user_call();\n/* USER CODE END 0 */\nint unsafe;\n/* USER CODE BEGIN 0 */')]
        for old, new in pairs:
            with self.subTest(old=old):
                self.assert_gate('Edit', {'file_path':str(self.main), 'old_string':old, 'new_string':new}, True)

    def test_cubemx_whole_write_is_denied(self):
        self.assert_gate('Write', {'file_path':str(self.main), 'content':SOURCE}, True)

    def test_missing_edit_data_is_denied(self):
        self.assert_gate('Edit', {'file_path':str(self.main), 'new_string':'unsafe'}, True)

    def test_application_write_and_allocation(self):
        self.assert_gate('Write', {'file_path':str(self.app), 'content':'void application(void) {}'}, False)
        for call in ['malloc(8)', 'pvPortMalloc(8)', 'free(ptr)', 'HAL_GPIO_WritePin(port, pin, 1)']:
            with self.subTest(call=call):
                self.assert_gate('Write', {'file_path':str(self.app), 'content':f'void application(void) {{ {call}; }}'}, True)

    def test_comments_and_strings_are_not_calls(self):
        self.assert_gate('Write', {'file_path':str(self.app), 'content':'/* malloc(8) */\nconst char *text="HAL_GPIO_WritePin()";'}, False)

    def test_windows_case_insensitive_path(self):
        if os.name != 'nt':
            self.skipTest('Requires case-insensitive Windows filesystem.')
        self.assert_gate('Edit', {'file_path':str(self.main).lower(), 'old_string':'int generated = 0;', 'new_string':'int generated = 1;'}, True)

    def test_protected_file_requires_manual_workflow(self):
        path = self.root / 'board.ld'
        path.write_text('MEMORY {}')
        self.assert_gate('Edit', {'file_path':str(path), 'old_string':'MEMORY {}', 'new_string':'MEMORY { FLASH: ORIGIN=0 }'}, True)


if __name__ == '__main__':
    unittest.main()
