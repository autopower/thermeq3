// JavaScript Document
var arr = [];
var tmp = [];
var owl_title = "";
var owl_text = "";
var j = [];

arr = JSON.parse(global("HTTPD"));

if (arr.value.length > 2) {
	tmp = arr.value.slice(1, -1).split(",");
} else {
	tmp = "";
}

if (tmp.length == 0) {
	owl_title = "Everything OK"
	owl_text = "All windows closed."
} else {
	owl_title = "Act now!"
	owl_text = tmp.length + " window(s) opened in room(s): "
	for (i=0; i < tmp.length; i++) {
		 j = tmp[i].split(":");
		 owl_text += " " + j[1].slice(2, -1);
	}
}