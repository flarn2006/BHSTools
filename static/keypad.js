window.onmessage = function(msg) {
	var lcdbits = [
		null, null, null, null, null, null, null, null,
		null, null, null, null, null, null, null, null,
		null, null, null, null, null, null, null, null,
		null, null, null, null, null, null, null, null,
		'i_not', 'i_ready', 'i_all', 'i_on', 'i_instant', 'i_door_chime', 'i_no_ac', 'i_motion_off',
		'i_trouble', 'i_test', 'i_line_cut', 'i_low_batt', 'i_alarm', 'i_memory', 'i_auxiliary_codes', 'i_canceled',
		'i_bypass', 'i_enter', 'i_master', 'i_user', 'i_call_brinks', 'i_zone', 'i_new', 'i_code',
		'i_area', 'i_number', 'i_envelope', 'i_time', null, null, null, null];
	
	for (var i=0; i<64; ++i) {
		if (lcdbits[i] != null) {
			var el = document.getElementById(lcdbits[i]);
			if (msg.data.keypad_lcd[i] == '1') {
				el.style.opacity = '1';
			} else {
				el.style.opacity = '0.1';
			}
		}
	}
};
