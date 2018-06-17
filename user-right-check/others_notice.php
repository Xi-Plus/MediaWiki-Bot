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

$config_page = file_get_contents($C["config_page_notice"]);
if ($config_page === false) {
	exit("get config failed\n");
}
$cfg = json_decode($config_page, true);

if (!$cfg["enable"]) {
	exit("disabled\n");
}

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($cfg["time_to_notice"]));
echo "timelimit < ".$timelimit." (".$cfg["time_to_notice"].")\n";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime AND `noticetime` < :noticetime ORDER BY `lasttime` ASC, `lastlog` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->bindValue(":noticetime", date("Y-m-d H:i:s", strtotime($cfg["time_for_do_not_notice_again"])));
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

echo "共有".count($row)."筆\n\n";
if (count($row) === 0) {
	exit("nothing to notice\n");
}

$count = 0;
$out = "";

$sthnot = $G["db"]->prepare("UPDATE `{$C['DBTBprefix']}userlist` SET `noticetime` = :noticetime WHERE `name` = :name");
$sthnot->bindValue(":noticetime", date("Y-m-d H:i:s"));
foreach ($row as $user) {
	echo $user["name"]."\t".$user["lastedit"]."\t".$user["lastlog"]."\t".$user["lastusergetrights"]."\n";
	for ($i=$C["fail_retry"]; $i > 0; $i--) {
		$starttimestamp = time();
		$page = "User_talk:".$user["name"];
		$res = cURL($C["wikiapi"]."?".http_build_query(array(
			"action" => "query",
			"prop" => "revisions",
			"format" => "json",
			"rvprop" => "content|timestamp",
			"titles" => $page
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		$pages = current($res["query"]["pages"]);
		if (isset($pages["missing"])) {
			$text = "";
			$basetimestamp = 0;
			$contentmodel = "wikitext";
		} else {
			$text = $pages["revisions"][0]["*"];
			$basetimestamp = $pages["revisions"][0]["timestamp"];
			$contentmodel = $pages["revisions"][0]["contentmodel"];
		}
		$isflow = ($contentmodel == "flow-board");

		if ($user["rights"] == ["ipblock-exempt"]) {
			if ($isflow) {
				$out = $cfg["notice_content_ipbe_flow"];
			} else {
				$out = $cfg["notice_content_ipbe"];
			}
			$topic = $cfg["notice_flow_topic_ipbe"];
		} else {
			$rightlist = "";
			foreach ($user["rights"] as $key => $value) {
				if ($key) {
					$rightlist .= "、";
				}
				if ($value == $C["AWBright"]) {
					$rightlist .= $cfg["right_awb_name"];
				} else {
					$rightlist .= '{{subst:int:group-'.$value.'}}';
				}
			}
			if ($isflow) {
				$out = sprintf($cfg["notice_content_flow"], $rightlist);
			} else {
				$out = sprintf($cfg["notice_content"], $rightlist);
			}
			$topic = sprintf($cfg["notice_flow_topic"], $rightlist);
		}

		if ($contentmodel == "wikitext") {
			$text .= "\n".$out;

			$summary = $cfg["notice_summary"];
			$post = array(
				"action" => "edit",
				"format" => "json",
				"title" => $page,
				"summary" => $summary,
				"text" => $text,
				"token" => $edittoken,
				"bot" => "",
				"starttimestamp" => $starttimestamp,
				"basetimestamp" => $basetimestamp
			);
			echo "edit ".$page." summary=".$summary."\n";
		} else if ($contentmodel == "flow-board") {
			$post = array(
				"action" => "flow",
				"format" => "json",
				"submodule" => "new-topic",
				"page" => $page,
				"token" => $edittoken,
				"nttopic" => $topic,
				"ntcontent" => $out,
				"ntformat" => "wikitext"
			);
			echo "edit ".$page." topic=".$topic."\n";
		} else {
			echo "cannot check contentmodel\n";
			break;
		}

		if (!$C["test"]) {
			$res = cURL($C["wikiapi"], $post);
		} else {
			$res = false;
			file_put_contents(__DIR__."/out.txt", $text);
		}
		$res = json_decode($res, true);
		if (isset($res["error"])) {
			echo "edit fail\n";
			var_dump($res);
			if ($i === 1) {
				echo "quit\n";
				break;
			} else {
				echo "retry\n";
			}
		} else {
			$count ++;
			$sthnot->bindValue(":name", $user["name"]);
			$res2 = $sthnot->execute();
			if ($res2 === false) {
				echo "update db fail\n";
			}
			break;
		}
	}
}
