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
	return $C['TIME_MIN'];
}

function lastlog($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "logevents",
		"leprop" => "type|timestamp",
		"leuser" => $username,
		"lelimit" => "1"
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	if (isset($res["query"]["logevents"][0]["type"]) && $res["query"]["logevents"][0]["type"] == "newusers") {
		return $C['TIME_MIN'];
	}
	if (isset($res["query"]["logevents"][0]["timestamp"])) {
		return date("Y-m-d H:i:s", strtotime($res["query"]["logevents"][0]["timestamp"]));
	}
	return $C['TIME_MIN'];
}

function userright($username, $checkawb = true) {
	global $C, $cfg;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "users",
		"usprop" => "groups",
		"ususers" => $username
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$rights = $res["query"]["users"][0]["groups"] ?? array();
	
	if ($checkawb) {
		$res2 = file_get_contents($cfg["AWBpage"]);
		if ($res2 === false) {
			exit("fetch page fail\n");
		}
		if (preg_match("/^\* *{$username} *$/m", $res2)) {
			$rights[]= $cfg["AWBright"];
		}
	}
		
	return $rights;
}

function lastusergetrights($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "logevents",
		"leprop" => "timestamp|user",
		"letype" => "rights",
		"letitle" => "User:".$username,
		"lelimit" => "10"
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	foreach ($res["query"]["logevents"] as $logevent) {
		if ($logevent["user"] !== "Jimmy-abot") {
			return date("Y-m-d H:i:s", strtotime($logevent["timestamp"]));
		}
	}
	return $C['TIME_MIN'];
}

function monthdiff($time) {
	$oy = date("Y", $time);
	$om = date("m", $time);
	$od = date("d", $time);
	$ny = date("Y");
	$nm = date("m");
	$nd = date("d");
	$res = $nm - $om;
	$res += ($ny - $oy) * 12;
	$res -= ($nd < $od);
	return $res;
}
