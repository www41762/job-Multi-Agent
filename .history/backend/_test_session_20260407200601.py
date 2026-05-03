"""E2E test for session management"""
from tools.db_memory import get_sql_memory_store, list_sql_sessions_rich

# Test rename + title + time
mem = get_sql_memory_store('test-mgmt-2')
mem.rename_session('AI Agent Engineer - ByteDance')
mem.add_chat_message('user', 'Hello')
mem.add_chat_message('assistant', 'Hi there')
mem.touch_updated()

info = mem.get_session_info()
print('Session info:', info)
assert info['title'] == 'AI Agent Engineer - ByteDance'

# Test rich list
all_sessions = list_sql_sessions_rich()
found = [s for s in all_sessions if s['session_id'] == 'test-mgmt-2']
assert len(found) == 1
assert found[0]['title'] == 'AI Agent Engineer - ByteDance'
assert found[0]['chat_count'] == 2
print('Rich list OK:', found[0])

# Test clear_chat_only
mem.clear_chat_only()
assert len(mem.get_chat_history()) == 0
info2 = mem.get_session_info()
assert info2['title'] == 'AI Agent Engineer - ByteDance'  # title preserved
print('Clear chat (keep title) OK')

# Cleanup
mem.clear()
print('Session management E2E test PASSED!')
