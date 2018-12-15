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

function updateDisplay()
{
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/display');
	xhr.onreadystatechange = function() {
		if (xhr.readyState === XMLHttpRequest.DONE) {
			if (xhr.status === 200) {
				var text = '';
				for (var i=0; i<64; i+=16) {
					if (i > 0) {
						text += '\n'
					}
					text += xhr.response.slice(i, i+16)
				}
				document.getElementById('screen').value = text;
			}
		}
	};
	xhr.send();
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
};
