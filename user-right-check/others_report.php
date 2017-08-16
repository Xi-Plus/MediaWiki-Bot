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
require(__DIR__."/function.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($C["other_report_timelimit"]));
echo "timelimit < ".$timelimit." (".$C["other_report_timelimit"].")\n";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime AND `noticetime` < '".date("Y-m-d H:i:s", time()-86400*7)."' ORDER BY `lasttime` ASC, `lastlog` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	$row[$key]["rights"] = explode("|", $row[$key]["rights"]);
	if (in_array("bot", $row[$key]["rights"])) {
		$row[$key]["rights"] = array_diff($row[$key]["rights"], ["AWB"]);
	}
	$row[$key]["rights"] = array_diff($row[$key]["rights"], $C["right-whitelist"]);
	$row[$key]["rights"] = array_values($row[$key]["rights"]);
	if (count($row[$key]["rights"]) == 0) {
		unset($row[$key]);
		continue;
	}
}
$row = array_values($row);

echo "共有".count($row)."筆\n\n";
if (count($row) === 0) {
	exit("nothing to report\n");
}

$count = 0;
$out = "";
foreach ($row as $user) {
	echo $user["name"]."\t".$user["lastedit"]."\t".$user["lastlog"]."\t".$user["lastusergetrights"]."\n";
	$count ++;
	$out .= "*{{User|".$user["name"]."}}
*:{{status2|新提案}}
*:需複審或解除之權限：";
foreach ($user["rights"] as $key => $value) {
	if ($key) {
		$out .= "、";
	}
	if ($value == $C["AWBright"]) {
		$out .= $C["AWBname"];
	} else {
		$out .= '{{subst:int:group-'.$value.'}}';
	}
}
$out .= "
*:理由：逾六個月沒有任何編輯活動、[[Special:用户贡献/".$user["name"]."|";
if ($user["lastedit"] == "0000-00-00 00:00:00") {
	$out .= "從未編輯過";
} else {
	$time = strtotime($user["lastedit"]);
	$out .= "最後編輯在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
$out .= "]]、[[Special:日志/".$user["name"]."|";
if ($user["lastlog"] == "0000-00-00 00:00:00") {
	$out .= "從未有日誌動作";
} else {
	$time = strtotime($user["lastlog"]);
	$out .= "最後日誌動作在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
}
$out .= "]]、[[Special:用户权限/".$user["name"]."|";
$time = strtotime($user["lastusergetrights"]);
$out .= "最後授權在".date("Y年n月j日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)";
$out .= "]]
*:~~~~

";
	if ($count >= $C["other_report_limit"]) {
		break;
	}
}

echo "press any key to continue\n";
fgets(STDIN);


for ($i=$C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $C["other_report_page"]
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	$start = strpos($text, $C["other_report_text"]);
	if ($start === false) {
		exit("split fail\n");
	}
	$newtext = substr($text, 0, $start).$out.substr($text, $start);

	$summary = $C["other_report_summary_prefix"];
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["other_report_page"],
		"summary" => $summary,
		"text" => $newtext,
		"token" => $edittoken,
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);

	echo "edit ".$C["other_report_page"]." summary=".$summary."\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__."/out.txt", $newtext);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		if ($i === 1) {
			exit("quit\n");
		} else {
			echo "retry\n";
		}
	} else {
		break;
	}
}
