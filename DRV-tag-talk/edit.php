<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");
@include(__DIR__."/function.php");
require(__DIR__."/../function/curl.php");
require(__DIR__."/../function/login.php");
require(__DIR__."/../function/edittoken.php");

echo "The time now is ".date("Y-m-d H:i:s")." (UTC)\n";

login();
$C["edittoken"] = edittoken();

# get previous process last revid
$lastrevidfile = __DIR__."/lastrevid.txt";
$lastrevid = @file_get_contents($lastrevidfile);
if ($lastrevid === false) {
	$lastrevid = 0;
}

# get page history (revid, user)
echo "lastrevid: ".$lastrevid."\n";
$res = cURL($C["wikiapi"]."?".http_build_query(array(
	"action" => "query",
	"format" => "json",
	"prop" => "revisions",
	"titles" => $C["from_page"],
	"rvprop" => "ids|user|timestamp",
	"rvlimit" => $C["rvlimit"]
)));
if ($res === false) {
	exit("fetch page fail\n");
}
$res = json_decode($res, true);
$page = current($res["query"]["pages"]);
$revs = $page["revisions"];
echo "get ".count($revs)." revisions\n";

# get all revid of archive bot edits
$arRevIndexs = [];
foreach ($revs as $index => $rev) {
	if ($rev["revid"] <= $lastrevid) {
		break;
	}
	if (in_array($rev["user"], $C["archviebotname"])) {
		$arRevIndexs []= $index;
	}
}

# foreach bot rev, get diff of content
foreach ($arRevIndexs as $index => $arRevIndex) {
	if ($index === end($arRevIndexs)) {
		break;
	}

	# get before and after archive revision content
	$beforeRevid = $revs[$arRevIndex+1]["revid"];
	$afterRevid = $revs[$arRevIndex]["revid"];
	echo "compare ".$beforeRevid." and ".$afterRevid."\n";

	$beforeRev = getrevcontent($beforeRevid);
	$afterRev = getrevcontent($afterRevid);

	$beforeStatus = getstatus($beforeRev);
	$afterStatus = getstatus($afterRev);

	$readytotag = [];
	foreach ($beforeStatus as $title => $status) {
		# if section removed and status = +
		if (!isset($afterStatus[$title]) && $status["result"]) {
			$info = getpageinfo($title);
			# page not exist, skip
			if ($info === false) {
				continue;
			}

			$talkpagecontent = getpagecontent($info["talk"]);
			# if talk page not exist, regarded as not tagged
			if ($talkpagecontent === false) {
				$istagged = false;
			} else {
				$istagged = checktalkpagetagged($talkpagecontent, $status["time"]);
			}

			# if tagged, skip
			if ($istagged) {
				echo $title." ".date("Y/m/d H:i", $status["time"])." tagged\n";
				continue;
			}

			$readytotag[$title] = $status;
			$readytotag[$title]["title"] = $info["title"];
			$readytotag[$title]["talk"] = $info["talk"];
		}
	}

	# foreach ready to tag section, find last status changed to + revid
	for ($curIndex=$arRevIndex+2; $curIndex < count($revs); $curIndex++) {
		if (count($readytotag) == 0) {
			break;
		}
		$curRevid = $revs[$curIndex]["revid"];
		$curRev = getrevcontent($curRevid);
		$curStatus = getstatus($curRev);
		foreach ($readytotag as $title => $status) {
			# if current rev is not status = +, tag the talk page
			if (isset($curStatus[$title]) && $curStatus[$title]["result"] === false) {
				echo $title;
				if ($title !== $status["title"]) {
					echo "->".$status["title"];
				}
				echo " (".$status["talk"].") ".$status["status"]." ".date("Y/m/d H:i", $status["time"])." ".$revs[$curIndex-1]["revid"]."\n";
				tagtalkpage($status["talk"], date("Y/m/d", $status["time"]), $revs[$curIndex-1]["revid"], $status["status"]);
				unset($readytotag[$title]);
			}
		}
	}
	echo "\n";
}

if (count($arRevIndexs)) {
	echo "update lastrevid to ".$revs[$arRevIndexs[0]]["revid"]."\n";
	file_put_contents($lastrevidfile, $revs[$arRevIndexs[0]]["revid"]);
} else {
	echo "no changed\n";
}

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
