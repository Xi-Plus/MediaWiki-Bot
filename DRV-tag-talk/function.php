<?php

# get wikitext of page by revid
function getrevcontent($revid) {
	global $C;
	$cachepath = $C["revcachedir"] . $revid . ".txt";
	if (file_exists($cachepath)) {
		$text = file_get_contents($cachepath);
		if ($text !== false) {
			return $text;
		}
	}
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content",
		"revids" => $revid,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	file_put_contents($cachepath, $text);
	return $text;
}

# solve redirect
function solveredirect($title) {
	global $C;
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"titles" => $title,
		"redirects" => 1,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	return $pages["title"];
}

# get wikitext of page by title
function getpagecontent($title) {
	global $C;

	if ($C["talkpagecache"]) {
		$cachepath = $C["revcachedir"] . $title . ".txt";
		if (file_exists($cachepath)) {
			$text = file_get_contents($cachepath);
			if ($text !== false) {
				return $text;
			}
		}
	}

	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"prop" => "revisions",
		"titles" => $title,
		"redirects" => true,
		"rvprop" => "content",
		"rvlimit" => 1,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	if (isset($pages["missing"])) {
		return false;
	}
	$text = $pages["revisions"][0]["*"];

	if ($C["talkpagecache"]) {
		file_put_contents($cachepath, $text);
	}

	return $text;
}

# split to content array by section from wikitext
function getstatus($text) {
	global $C;
	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^(==.+?==\s*)$/m", $hash . "$1", $text);
	$text = explode($hash, $text);
	unset($text[0]);
	$result = [];
	foreach ($text as $temp) {
		if (preg_match("/^==\s*\[\[:?([^]]+)]]\s*==\s*$/m", $temp, $m)) {
			$title = $m[1];
		} else if (preg_match("/^==\s*\[\[:?[^]]+]]\s*→\s*\[\[:?([^]]+)]]\s*==\s*$/m", $temp, $m)) {
			$title = $m[1];
		} else {
			if ($C["errormessage"]) {
				echo "bad title: " . explode("\n", trim($temp))[0] . "\n";
			}
			continue;
		}
		if (preg_match("/{{Status2\|(?:\+|Done|完成)\|?(?:2=)?(.*?)}}/i", $temp, $m)) {
			$status = trim($m[1]);
			if ($status === "") {
				$status = "完成";
			}
			$ok = true;
		} else if (preg_match("/{{Status2\|(?:-|Not done|拒絕|拒绝|驳回|駁回|未完成)\|?(?:2=)?(.*?)}}/i", $temp, $m)) {
			$status = trim($m[1]);
			if ($status === "") {
				$status = "未完成";
			}
			$ok = false;
		} else if (preg_match("/{{Status2\|(?:新申請|on hold|擱置|搁置|等待|等待中|OH|Hold|\*|\?)\|?(?:2=)?(.*?)}}/i", $temp, $m)) {
			$status = trim($m[1]);
			$ok = false;
		} else {
			if ($C["errormessage"]) {
				echo "cannot match status:\n";
				echo trim($temp) . "\n";
			}
			$status = "未知";
			$ok = false;
		}
		$time = getfirsttime($temp);

		# status=+ override status=-, but status=- not override status=+
		if (!isset($result[$title]) || (isset($result[$title]) && $result[$title]["result"] === false)) {
			$result[$title] = [
				"title" => $title,
				"result" => $ok,
				"status" => $status,
				"time" => $time,
			];
		}
	}
	return $result;
}

# convert time string to timestamp
function converttime($chitime) {
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) (\d{2})\:(\d{2}) \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1] . "/" . $m[2] . "/" . $m[3] . " " . $m[4] . ":" . $m[5]);
	} else {
		exit("converttime fail\n");
	}
}

# get first timestamp of sign from wikitext
function getfirsttime($text) {
	if (preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $text, $m)) {
		$firsttime = time();
		foreach ($m[0] as $timestr) {
			$time = converttime($timestr);
			if ($time < $firsttime) {
				$firsttime = $time;
			}

		}
		return $firsttime;
	}
	echo "cannot get firsttime:\n";
	echo trim($text) . "\n";
	return false;
}

# check page exist, solve converttitle and redirect, get talk page title
function getpageinfo($pagename) {
	global $C, $cfg;
	if (!isset($C["ns"])) {
		$C["ns"] = [];

		$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
			"action" => "query",
			"format" => "json",
			"meta" => "siteinfo",
			"siprop" => "namespaces",
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);

		foreach ($res["query"]["namespaces"] as $ns => $value) {
			$C["ns"][$ns] = $value["*"];
		}
	}

	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"prop" => "info",
		"titles" => $pagename,
		"converttitles" => true,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$page = current($res["query"]["pages"]);

	if (isset($page["missing"])) {
		echo $pagename . " missing\n";
		return false;
	}

	if (in_array($page["ns"], $cfg["nsignore"])) {
		echo $pagename . "in ignore ns (" . $page["ns"] . ")\n";
		return false;
	}
	if ($page["ns"] % 2 == 1) {
		return [
			"title" => $page["title"],
			"talk" => $page["title"],
		];
	} else if ($page["ns"] == 0) {
		return [
			"title" => $page["title"],
			"talk" => solveredirect("Talk:" . $page["title"]),
		];
	} else {
		$talk = preg_replace("/^" . $C["ns"][$page["ns"]] . ":/", $C["ns"][$page["ns"] + 1] . ":", $page["title"]);
		return [
			"title" => $page["title"],
			"talk" => solveredirect($talk),
		];
	}
}

function checktalkpagetagged($text, $date) {
	$regdate1 = date("Y", $date) . "\/?0?" . date("n", $date) . "\/?0?" . date("j", $date);
	$regdate2 = date("Y", $date) . "-0?" . date("n", $date) . "-0?" . date("j", $date);
	$regdate3 = date("Y", $date) . "年0?" . date("n", $date) . "月0?" . date("j", $date) . "日";

	if (preg_match("/{{\s*Drv-kept\s*\|\s*({$regdate1}|{$regdate2})/i", $text)) {
		return true;
	}

	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^(==.+?==\s*)$/m", $hash . "$1", $text);
	$text = explode($hash, $text)[0];

	if (preg_match("/({$regdate1}|{$regdate2}|{$regdate3}).*(存廢覆核|存废复核)/i", $text)) {
		return true;
	}
	if (preg_match("/(存廢覆核|存废复核).*({$regdate1}|{$regdate2}|{$regdate3})/i", $text)) {
		return true;
	}
	return false;
}

function tagtalkpage($title, $date, $diff, $result) {
	global $C, $cfg;
	if (trim($title) === "") {
		echo "bad title\n";
		return false;
	}
	if (trim($result) === "") {
		$result = "完成";
	}
	$add = "{{Drv-kept|$date|$diff|$result}}";
	echo $add . "\n";
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"prop" => "info",
		"titles" => $title,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$page = current($res["query"]["pages"]);
	if ($page["ns"] % 2 !== 1) {
		echo "not talk ns\n";
		return false;
	}

	$starttimestamp = time();
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $title,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$page = current($res["query"]["pages"]);
	if (isset($page["missing"])) {
		$text = "";
		$basetimestamp = 0;
		echo $title . " missing\n";
	} else {
		$text = $page["revisions"][0]["*"];
		$basetimestamp = $page["revisions"][0]["timestamp"];
	}

	$text = $add . "\n" . trim($text);

	$summary = sprintf($cfg["summary"],
		"[[Special:diff/" . $diff . "|" . $result . "]]");
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $title,
		"summary" => $summary,
		"text" => $text,
		"token" => $C["edittoken"],
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp,
	);
	echo "edit " . $title . " summary=" . $summary . "\n";

	$check = "";
	while ($C["checkedit"] && $check !== "y") {
		echo "continue? (y/n) ";
		$check = strtolower(trim(fgets(STDIN)));
		if ($check === "n") {
			echo "skip\n";
			return;
		}
	}

	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__ . "/" . str_replace(":", "_", $title) . ".txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		var_dump($res);
		return false;
	} else {
		if ($C["talkpagecache"]) {
			$cachepath = $C["revcachedir"] . $title . ".txt";
			if (file_exists($cachepath)) {
				unlink($cachepath);
			}
		}
		return true;
	}
}
