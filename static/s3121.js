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

function makenbsp(str)
{
	return str.replace(/\s/g, '\xa0');
}

function updateDisplay()
{
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/display');
	xhr.onreadystatechange = function() {
		if (xhr.readyState === XMLHttpRequest.DONE) {
			if (xhr.status === 200) {
				document.getElementById('line1').innerText = makenbsp(xhr.response.slice(0, 16));
				document.getElementById('line2').innerText = makenbsp(xhr.response.slice(16, 32));
				document.getElementById('line3').innerText = makenbsp(xhr.response.slice(32, 48));
				document.getElementById('line4').innerText = makenbsp(xhr.response.slice(48));
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
