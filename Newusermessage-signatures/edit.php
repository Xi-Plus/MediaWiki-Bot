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

for ($i=0; $i < $C["fail_retry"]; $i++) { 
	$text = file_get_contents($C["page"]);
	if ($text === false) {
		echo "fetch fail\n";
		continue;
	}

	preg_match_all("/^(\* |: inactive\||: nouser\|)(.+)$/m", $text, $m);
	$out = '{| class="wikitable sortable"
!使用者
!簽名
!狀態
!字數
!位元組
';
	foreach ($m[0] as $key => $temp) {
		$status = $m[1][$key];
		if ($status[0] === "*") {
			$status = "";
		} else {
			$status = substr($status, 2, -1);
		}
		$sign = $m[2][$key];
		$user = "";
		if (preg_match_all("/\[\[(?:User:|用户:|User talk:|User_talk:|用户讨论:|Special:Contributions\/|Special:用户贡献\/|Special:用戶貢獻\/|特殊:用户贡献\/|特殊:用戶貢獻\/)([^|\/]+)/i", $sign, $m2)) {
			$user = "{{User|".$m2[1][0]."}}";
		}
		$len = mb_strlen($sign);
		$byte = strlen($sign);
		if ($byte > 255) {
			$byte = "{{red|'''".$byte."'''}}";
		}
		$out .= '|-
|'.$user.'
| '.$sign.'
|'.$status.'
|'.$len.'
|'.$byte.'
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
		continue;
	}

	break;
}
