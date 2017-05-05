<?php
function userid($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "users",
		"ususers" => $username
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	return $res["query"]["users"][0]["userid"] ?? 0;
}

function lastedit($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "usercontribs",
		"uclimit" => "1",
		"ucuser" => $username,
		"ucprop" => "timestamp"
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	if (isset($res["query"]["usercontribs"][0]["timestamp"])) {
		return date("Y-m-d H:i:s", strtotime($res["query"]["usercontribs"][0]["timestamp"]));
	}
	return "0000-00-00 00:00:00";
}

function lastlog($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "logevents",
		"leprop" => "timestamp",
		"leuser" => $username,
		"lelimit" => "1"
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	if (isset($res["query"]["logevents"][0]["timestamp"])) {
		return date("Y-m-d H:i:s", strtotime($res["query"]["logevents"][0]["timestamp"]));
	}
	return "0000-00-00 00:00:00";
}

function userright($username) {
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "users",
		"usprop" => "groups",
		"ususers" => $bot["name"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	return $res["query"]["users"][0]["groups"] ?? array();
}
