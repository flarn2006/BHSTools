window.onmessage = function(msg) {
	var lcdbits = [
		'colon', 'digit0b', 'digit0c', 'am', 'pm', null, null, null,
		'digit1a', 'digit1b', 'digit1c', 'digit1d', 'digit1e', 'digit1f', 'digit1g', null,
		'digit2a', 'digit2b', 'digit2c', 'digit2d', 'digit2e', 'digit2f', 'digit2g', null,
		'digit3a', 'digit3b', 'digit3c', 'digit3d', 'digit3e', 'digit3f', 'digit3g', null,
		'i_not', 'i_ready', 'i_all', 'i_on', 'i_instant', 'i_door_chime', 'i_no_ac', 'i_motion_off',
		'i_trouble', 'i_test', 'i_line_cut', 'i_low_batt', 'i_alarm', 'i_memory', 'i_auxiliary_codes', 'i_canceled',
		'i_bypass', 'i_enter', 'i_master', 'i_user', 'i_call_brinks', 'i_zone', 'i_new', 'i_code',
		'i_area', 'i_number', 'i_envelope', 'i_time', null, null, null, null];
	
	var svg = document.getElementById('num_svg');
	for (var i=0; i<64; ++i) {
		if (lcdbits[i] != null) {
			var id = lcdbits[i];
			var el;
			if (id.startsWith('i_')) {
				el = document.getElementById(id);
			} else {
				el = svg.contentDocument.getElementById(id);
			}
			if (msg.data.keypad_lcd[i] == '1') {
				el.style.opacity = '1';
			} else {
				el.style.opacity = '0.1';
			}
		}
	}
};
