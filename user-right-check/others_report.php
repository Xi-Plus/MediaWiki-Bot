<?php
require __DIR__ . "/../config/config.php";
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include __DIR__ . "/config.php";
require __DIR__ . "/../function/curl.php";
require __DIR__ . "/../function/login.php";
require __DIR__ . "/../function/edittoken.php";
require __DIR__ . "/function.php";

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

$config_page = file_get_contents($C["config_page_report"]);
if ($config_page === false) {
	exit("get config failed\n");
}
$cfg = json_decode($config_page, true);

if (!$cfg["enable"]) {
	exit("disabled\n");
}

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($cfg["other_report_timelimit"]));
echo "timelimit < " . $timelimit . " (" . $cfg["other_report_timelimit"] . ")\n";
$notice_timelimit = date("Y-m-d H:i:s", strtotime($cfg["other_report_notice_timelimit"]));
echo "notice_timelimit < " . $notice_timelimit . " (" . $cfg["other_report_notice_timelimit"] . ")\n";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime AND `noticetime` != '{$C['TIME_MIN']}' AND `noticetime` < :noticetime ORDER BY `lasttime` ASC, `lastlog` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->bindValue(":noticetime", $notice_timelimit);
$sth->execute();
$row = $sth->fetchAll(PDO::FETCH_ASSOC);

foreach ($row as $key => $user) {
	$row[$key]["rights"] = explode("|", $row[$key]["rights"]);
	if (in_array("bot", $row[$key]["rights"])) {
		$row[$key]["rights"] = array_diff($row[$key]["rights"], ["AWB"]);
	}
	$row[$key]["rights"] = array_diff($row[$key]["rights"], $cfg["right_not_to_process"]);
	$row[$key]["rights"] = array_values($row[$key]["rights"]);
	if (count($row[$key]["rights"]) == 0) {
		unset($row[$key]);
		continue;
	}
}
$row = array_values($row);

echo "共有" . count($row) . "筆\n\n";
if (count($row) === 0) {
	exit("nothing to report\n");
}

for ($i = $C["fail_retry"]; $i > 0; $i--) {
	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $cfg["other_report_page"],
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	$basetimestamp = $pages["revisions"][0]["timestamp"];
	echo "get main page\n";

	$start = strpos($text, $cfg["other_report_text"]);
	if ($start === false) {
		exit("split fail\n");
	}

	$count = 0;
	$out = "";
	foreach ($row as $user) {
		echo $user["name"] . "\t" . $user["lastedit"] . "\t" . $user["lastlog"] . "\t" . $user["lastusergetrights"];
		if (strpos($text, "{{User|" . $user["name"] . "}}") !== false) {
			echo "\talready report\n";
			continue;
		}
		$count++;
		$out .= "*{{User|" . $user["name"] . "}}\n*:{{Status|新提案}}\n*:需複審或解除之權限：";
		foreach ($user["rights"] as $key => $value) {
			if ($key) {
				$out .= "、";
			}
			if ($value == $cfg["right_awb_name"]) {
				$out .= $cfg["right_text"]["AWB"];
			} else {
				$out .= '{{subst:int:group-' . $value . '}}';
			}
		}
		$out .= "\n*:理由：逾六個月沒有任何編輯活動、[[Special:用户贡献/" . $user["name"] . "|";
		if ($user["lastedit"] == $C['TIME_MIN']) {
			$out .= "從未編輯過";
		} else {
			$time = strtotime($user["lastedit"]);
			$out .= "最後編輯在" . date("Y年n月j日", $time) . " (" . $C["day"][date("w", $time)] . ") " . date("H:i", $time) . " (UTC)";
		}
		$out .= "]]、[[Special:日志/" . $user["name"] . "|";
		if ($user["lastlog"] == $C['TIME_MIN']) {
			$out .= "從未有日誌動作";
		} else {
			$time = strtotime($user["lastlog"]);
			$out .= "最後日誌動作在" . date("Y年n月j日", $time) . " (" . $C["day"][date("w", $time)] . ") " . date("H:i", $time) . " (UTC)";
		}
		$out .= "]]";
		if ($user["lastusergetrights"] != $C['TIME_MIN']) {
			$time = strtotime($user["lastusergetrights"]);
			$out .= "、[[Special:用户权限/" . $user["name"] . "|最後授權在" . date("Y年n月j日", $time) . " (" . $C["day"][date("w", $time)] . ") " . date("H:i", $time) . " (UTC)]]";
		}
		$out .= "\n*:<small>如果最後編輯時間不正確，請'''務必'''通知機器人操作者。</small>--~~~~\n\n";
		echo "\n";

		if ($count >= $cfg["other_report_limit"]) {
			break;
		}
	}

	if ($out === "") {
		exit("nothing to report\n");
	}

	if ($C["check"]) {
		echo "press any key to continue\n";
		fgets(STDIN);
	}

	$newtext = substr($text, 0, $start) . $out . substr($text, $start);

	$summary = $cfg["other_report_summary_prefix"] . "，共" . $count . "位用戶";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $cfg["other_report_page"],
		"summary" => $summary,
		"text" => $newtext,
		"token" => $edittoken,
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);

	echo "edit " . $cfg["other_report_page"] . " summary=" . $summary . "\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__ . "/out.txt", $newtext);
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
