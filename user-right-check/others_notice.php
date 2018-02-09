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

login("bot");
$edittoken = edittoken();

$timelimit = date("Y-m-d H:i:s", strtotime($C["other_notice_timelimit1"]));
echo "timelimit < ".$timelimit." (".$C["other_notice_timelimit1"].")\n";

$sth = $G["db"]->prepare("SELECT * FROM `{$C['DBTBprefix']}userlist` WHERE `lasttime` < :lasttime AND `noticetime` < :noticetime ORDER BY `lasttime` ASC, `lastlog` ASC");
$sth->bindValue(":lasttime", $timelimit);
$sth->bindValue(":noticetime", date("Y-m-d H:i:s", strtotime($C["other_notice_timelimit2"])));
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
			$out = "{{subst:inactive IPBE".($isflow?"|flow=1|sig=n":"")."}}";
			$topic = "因不活躍而取消[[WP:IPBE|IP封禁例外]]權限的通知";
		} else {
			$out = "{{subst:inactive right".($isflow?"|flow=1|sig=n":"")."|";
			$topic = "因不活躍而取消";
			foreach ($user["rights"] as $key => $value) {
				if ($key) {
					$out .= "、";
					$topic = "、";
				}
				if ($value == $C["AWBright"]) {
					$out .= $C["AWBname"];
					$topic = $C["AWBname"];
				} else {
					$out .= '{{subst:int:group-'.$value.'}}';
					$topic = '{{subst:int:group-'.$value.'}}';
				}
			}
			$out .= "}}";
			$topic .= "權限的通知";
		}

		if ($contentmodel == "wikitext") {
			$text .= "\n".$out;

			$summary = $C["other_notice_summary_prefix"];
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
	if ($count >= $C["other_notice_limit"]) {
		break;
	}
}
