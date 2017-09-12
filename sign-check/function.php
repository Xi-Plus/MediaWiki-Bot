<?php
function lastedit($username) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "usercontribs",
		"uclimit" => "1",
		"ucuser" => $username,
		"ucprop" => "timestamp",
		"ucnamespace" => "1|3|4|5|7|9|11|13|15|101|119|829|2600"
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
