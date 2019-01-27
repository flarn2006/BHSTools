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
