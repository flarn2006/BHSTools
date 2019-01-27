var display = null;
var lastCursorPos = null;
var cursorBlink = true;
var cursorBlinkIntervalID = null;

function sendKey(code)
{
	var xhr = new XMLHttpRequest();
	xhr.open('POST', '/key');
	xhr.onreadystatechange = function() {
		if (xhr.readyState === XMLHttpRequest.DONE) {
			setTimeout(updateDisplay, 100);
		}
	};
	xhr.send(code.toString(16))
}

function resetCursorBlink()
{
	cursorBlink = true;
	clearInterval(cursorBlinkIntervalID);
	cursorBlinkIntervalID = setInterval(function() {
		cursorBlink = !cursorBlink;
		showDisplay();
	}, 500);
}

function updateDisplay()
{
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/status');
	xhr.onreadystatechange = function() {
		if (xhr.readyState === XMLHttpRequest.DONE) {
			if (xhr.status === 200) {
				display = JSON.parse(xhr.response);
				if (lastCursorPos != display.cursor.pos) {
					lastCursorPos = display.cursor.pos;
					resetCursorBlink();
				}
				showDisplay();
			}
		}
	};
	xhr.send();
}

function showDisplay()
{
	var disp_with_cursor = display.text;
	if (cursorBlink && display.cursor.visible) {
		disp_with_cursor = disp_with_cursor.slice(0, display.cursor.pos) + '█' + disp_with_cursor.slice(display.cursor.pos + 1)
	}

	var text = '';
	for (var i=0; i<64; i+=16) {
		if (i > 0) {
			text += '\n'
		}
		text += disp_with_cursor.slice(i, i+16)
	}
	document.getElementById('screen').value = text;
}

window.onload = function() {
	[].forEach.call(document.querySelectorAll('button[data-keycode]'), function(btn) {
		var keycode = parseInt('0x' + btn.getAttribute('data-keycode'));
		btn.onmousedown = function() {
			sendKey(keycode | 0x80);
		};
		btn.onmouseup = function() {
			sendKey(keycode);
		};
	});

	setInterval(updateDisplay, 500);
	resetCursorBlink();

	var tools = document.getElementById('tools');
	var links = tools.getElementsByTagName('a');
	[].forEach.call(links, function(el) {
		el.addEventListener('click', function() {
			if (el.classList.contains('selected')) {
				el.classList.remove('selected');
				tools.classList.remove('active');
			} else {
				tools.classList.add('active');
				[].forEach.call(links, function(el2) {
					if (el === el2) {
						el2.classList.add('selected');
					} else {
						el2.classList.remove('selected');
					}
				});
			}
		});
	});
};
