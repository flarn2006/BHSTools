function export_json()
{
	var list = [].map.call(document.body.getElementsByTagName('section'), function(el) {
		var cmd = parseInt(el.getAttribute('data-cmd'));
		var arg = el.getAttribute('data-arg');
		return {cmd:cmd, arg:arg};
	});

	var obj = [{version:0, data:list}];

	var blob = new Blob([JSON.stringify(obj)], {type:'application/json'});
	location.href = URL.createObjectURL(blob);
}
