<?php
function edittoken() {
	global $C;
	$post = array(
		"action" => "query",
		"meta" => "tokens",
		"type" => "csrf"
	);
	$res = cURL($C["wikiapi"]."?action=login&format=json", $post);
	if ($res === false) {
		exit("fetch page error\n");
	}
	$res = json_decode($res, true);
	if (isset($res["query"]["tokens"]["csrftoken"])){
		return $res["query"]["tokens"]["csrftoken"];
	} else {
		exit("get edittoken fail \n");
	}
}
