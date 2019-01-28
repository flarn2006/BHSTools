// In case you're curious about the filename, it's a reference to the official downloading software, known as Vivaldi.
// (If anyone knows where I can find a copy of that software, please let me know!)

var intervalID = null;
var lastBlockList = [];

function updateStatus()
{
	var icode_out = document.getElementById('icode');
	var blocks_out = document.getElementById('blocks');
	var xhr = new XMLHttpRequest();
	xhr.open('GET', '/download_status');
	xhr.onreadystatechange = function() {
		if (xhr.readyState === XMLHttpRequest.DONE && xhr.status == 200) {
			var s = JSON.parse(xhr.response);
			if (s.icode) {
				icode_out.innerText = s.icode;
			} else {
				icode_out.innerText = '(not yet known)';
			}
			var addBlocks = function(textlist) {
				textlist.forEach(function(blockdesc) {
					var el = document.createElement('li');
					el.innerText = blockdesc;
					blocks_out.appendChild(el);
				});
			};
				
			var newCount = s.blocks.length - lastBlockList.length;
			if (newCount > 0) {
				addBlocks(s.blocks.slice(-newCount));
			} else if (newCount < 0) {
				blocks_out.innerHTML = '';
				addBlocks(s.blocks);
			}
			lastBlockList = s.blocks;
		}
	};
	xhr.send();
}

window.onload = function() {
	var btn = document.getElementById('dlstart');
	btn.addEventListener('click', function() {
		var xhr = new XMLHttpRequest();
		xhr.open('POST', '/start_download');
		xhr.onreadystatechange = function() {
			if (xhr.readyState === XMLHttpRequest.DONE) {
				btn.innerText = 'Restart';
			}
		};
		xhr.send('');
	});
	setInterval(updateStatus, 250);
};
