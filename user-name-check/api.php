<?php
require_once(__DIR__.'/../config/config.php');
date_default_timezone_set('UTC');
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");

$response = [];
if (!isset($_GET["user"]) || $_GET["user"] === "") {
	$response["error"] = "wrong user";
	echo json_encode($response);
	exit;
} else {
	$checkuser = $_GET["user"];
}

$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "antispoof",
	"format" => "json",
	"username" => $checkuser
)));
if ($res === false) {
	$response["error"] = "format username fail";
	echo json_encode($response);
	exit;
}

if (isset($_GET["limit_levenshtein"]) && is_numeric($_GET["limit_levenshtein"])) {
	$C["limit"]["levenshtein"] = (int)($_GET["limit_levenshtein"]);
}
$response["limit_levenshtein"] = $C["limit"]["levenshtein"];

if (isset($_GET["limit_similar_text"]) && is_numeric($_GET["limit_similar_text"])) {
	$C["limit"]["similar_text"] = (int)($_GET["limit_similar_text"]);
}
$response["limit_similar_text"] = $C["limit"]["similar_text"];

if (isset($_GET["limit_similar_text_precent"]) && is_numeric($_GET["limit_similar_text_precent"])) {
	$C["limit"]["similar_text_precent"] = (int)($_GET["limit_similar_text_precent"]);
}
$response["limit_similar_text_precent"] = $C["limit"]["similar_text_precent"];

if (isset($_GET["limit_count"]) && is_numeric($_GET["limit_count"]) && (int)($_GET["limit_count"]) <= $C["limit"]["count"]) {
	$C["limit"]["count"] = (int)($_GET["limit_count"]);
}
$response["limit_count"] = $C["limit"]["count"];

$res = json_decode($res, true);
if (isset($res["antispoof"]["normalised"])) {
	$checkuser = substr($res["antispoof"]["normalised"], 3);
} else {
	$checkuser = "";
}

$response["user"] = $checkuser;

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}`");
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);
$userlist = array();
$minl = 1000;
$minname = "";
$maxpercent = 0;
$maxname = "";
foreach ($row as $key => $user) {
	$row[$key]["levenshtein"] = levenshtein($checkuser, $row[$key]["normalised"]);
	$row[$key]["similar_text"] = similar_text($checkuser, $row[$key]["normalised"], $row[$key]["similar_text_precent"]);
}

function cmplevenshtein($a, $b) {
	if ($a["levenshtein"] == $b["levenshtein"]) {
		return ($a["name"] < $b["name"]) ? -1 : 1;
	}
    return ($a["levenshtein"] < $b["levenshtein"]) ? -1 : 1;
}
usort($row, 'cmplevenshtein');

$response["levenshtein"] = [];
for ($i=0; $i < $C["limit"]["count"] && $row[$i]["levenshtein"] <= $C["limit"]["levenshtein"]; $i++) {
	$response["levenshtein"] []= ["user"=>$row[$i]["name"], "value"=>$row[$i]["levenshtein"]];
}

function cmpsimilar_text($a, $b) {
	if ($a["similar_text"] == $b["similar_text"]) {
		return ($a["name"] < $b["name"]) ? -1 : 1;
	}
    return ($a["similar_text"] > $b["similar_text"]) ? -1 : 1;
}
usort($row, 'cmpsimilar_text');

$response["similar_text"] = [];
for ($i=0; $i < $C["limit"]["count"] && $row[$i]["similar_text"] >= $C["limit"]["similar_text"]; $i++) {
	$response["similar_text"] []= ["user"=>$row[$i]["name"], "value"=>$row[$i]["similar_text"]];
}

function cmpsimilar_text_precent($a, $b) {
	if ($a["similar_text_precent"] == $b["similar_text_precent"]) {
		return ($a["name"] < $b["name"]) ? -1 : 1;
	}
    return ($a["similar_text_precent"] > $b["similar_text_precent"]) ? -1 : 1;
}
usort($row, 'cmpsimilar_text_precent');

$response["similar_text_precent"] = [];
for ($i=0; $i < $C["limit"]["count"] && $row[$i]["similar_text_precent"] >= $C["limit"]["similar_text_precent"]; $i++) {
	$response["similar_text_precent"] []= ["user"=>$row[$i]["name"], "value"=>$row[$i]["similar_text_precent"]];
}

echo json_encode($response);
