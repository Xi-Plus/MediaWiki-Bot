<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"list" => "abusefilters",
	"abflimit" => "max",
	"abfprop" => "id|description|actions|status|private|hits"
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);

$out = '__NOINDEX__
{| class="wikitable sortable" style="background-color: #fff;"
|- 
! style="background-color: #ddf;"| {{int:abusefilter-list-id}}
! style="background-color: #ddf;"| {{int:abusefilter-list-public}}
! style="background-color: #ddf;"| {{int:abusefilter-list-consequences}}
! style="background-color: #ddf;"| {{int:abusefilter-list-status}}
! style="background-color: #ddf;"| {{int:abusefilter-list-visibility}}
! style="background-color: #ddf;"| {{int:abusefilter-list-hitcount}}
';
foreach ($res["query"]["abusefilters"] as $AF) {
	$action = $AF["actions"];
	$action = str_replace("warn", "{{int:abusefilter-action-warn}}", $action);
	$action = str_replace("tag", "{{int:abusefilter-action-tag}}", $action);
	$action = str_replace("disallow", "{{int:abusefilter-action-disallow}}", $action);
	$action = str_replace("throttle", "{{int:abusefilter-action-throttle}}", $action);
	$action = str_replace("blockautopromote", "{{int:abusefilter-action-blockautopromote}}", $action);
	$action = str_replace(",", "、", $action);
	$out .= '|- style="color: '.(isset($AF["enabled"])?"#000":(isset($AF["deleted"])?"#aaa":"#666")).';"
| [[Special:AbuseFilter/'.$AF["id"].'|'.$AF["id"].']]
| [[Special:AbuseFilter/'.$AF["id"].'|'.$AF["description"].']]
|'.$action.'
|'.(isset($AF["enabled"])?"{{int:abusefilter-enabled}}":(isset($AF["deleted"])?"{{int:abusefilter-deleted}}":"{{int:abusefilter-disabled}}")).'
|'.(isset($AF["private"])?"{{int:abusefilter-hidden}}":"{{int:abusefilter-unhidden}}").'
|data-sort-value='.$AF["hits"].'| [{{fullurl:Special:AbuseLog|wpSearchFilter='.$AF["id"].'}} {{int:abusefilter-hitcount|'.$AF["hits"].'}}]
';
}
$out .= '|}';

$summary = $C["summary_prefix"]."更新";
$post = array(
	"action" => "edit",
	"format" => "json",
	"title" => $C["outpage"],
	"summary" => $summary,
	"text" => $out,
	"minor" => "",
	"token" => $edittoken
);
echo "edit ".$C["outpage"]." summary=".$summary."\n";
if (!$C["test"]) {
	$res = cURL($C["wikiapi"], $post);
} else {
	$res = false;
	file_put_contents(__DIR__."/out.txt", $out);
}
$res = json_decode($res, true);
if (isset($res["error"])) {
	echo "edit fail\n";
}
