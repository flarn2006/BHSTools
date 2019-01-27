// In case you're curious about the filename, it's a reference to the official downloading software, known as Vivaldi.
// (If anyone knows where I can find a copy of that software, please let me know!)

window.onload = function() {
	document.getElementById('dlstart').addEventListener('click', function() {
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/start_download');
		xhr.onreadystatechange = function() {
			if (xhr.readyState === XMLHttpRequest.DONE) {
				// TODO; do something here
			}
		};
		xhr.send('');
	});
	document.getElementById('dlresume').addEventListener('click', function() {
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/resume_download');
		xhr.onreadystatechange = function() {
			if (xhr.readyState === XMLHttpRequest.DONE) {
				// TODO; do something here
			}
		};
		xhr.send('');
	});
};
