<?php
require_once __DIR__ . '/curl.php';

function getPage($api, $title) {
	$res = cURL($api . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $title,
	)));
	if ($res === false) {
		return false;
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	return $pages;
}

function getPageContent($api, $title) {
	$res = getPage($api, $title);
	if (!isset($res["revisions"][0])) {
		return false;
	}
	return $res["revisions"][0];
}
