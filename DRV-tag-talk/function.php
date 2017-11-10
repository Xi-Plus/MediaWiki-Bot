<?php

function parsediff($diff) {
	$diff = str_replace('<del class="diffchange diffchange-inline">', "", $diff);
	$diff = str_replace('</del>', "", $diff);
	$diff = str_replace('<ins class="diffchange diffchange-inline">', "", $diff);
	$diff = str_replace('</ins>', "", $diff);

	if (preg_match('/diff-deletedline"><div>\*{{Status2\|(新申請|on hold|擱置|搁置|等待|等待中|OH|oh|hold|Hold|\*|\?).*?}}/', $diff) && preg_match('/diff-addedline"><div>\*{{Status2\|(?:\+|Done|done|完成)\|?(.*?)}}/', $diff, $m)) {
		$status = $m[1];
		preg_match_all('/<div>(== *\[\[:?([^\]]+?)]] *==)<\/div>/', $diff, $m);
		$section = $m[1][1];
		$page = $m[2][1];
		return ["result"=>true, "status"=>$status, "page"=>$page, "section"=>$section];
	} else {
		return ["result"=>false];
	}
}

function getrevcontent($revid) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content",
		"revids" => $revid
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$pages = current($res["query"]["pages"]);
	$text = $pages["revisions"][0]["*"];
	return $text;
}

function converttime($chitime){
	if (preg_match("/(\d{4})年(\d{1,2})月(\d{1,2})日 \(.{3}\) (\d{2})\:(\d{2}) \(UTC\)/", $chitime, $m)) {
		return strtotime($m[1]."/".$m[2]."/".$m[3]." ".$m[4].":".$m[5]);
	} else {
		exit("converttime fail\n");
	}
}

function getfirsttime($text, $section) {
	$hash = md5(uniqid(rand(), true));
	$text = preg_replace("/^( *==.+?== *)$/m", $hash."$1", $text);
	$text = explode($hash, $text);
	foreach ($text as $temp) {
		if (strpos($temp, $section) !== false) {
			preg_match_all("/\d{4}年\d{1,2}月\d{1,2}日 \(.{3}\) \d{2}\:\d{2} \(UTC\)/", $temp, $m);
			$firsttime = time();
			foreach ($m[0] as $timestr) {
				$time = converttime($timestr);
				if ($time < $firsttime) $firsttime = $time;
			}
			return $firsttime;
		}
	}
	echo "not found!\n";
	return false;
}

function tagtalkpage($title, $date, $diff, $result) {
	global $C;
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"format" => "json",
		"prop" => "info",
		"titles" => $title,
		"redirects" => 1,
		"converttitles" => 1
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$page = current($res["query"]["pages"]);
	if (isset($page["missing"])) {
		echo "page not found\n";
		return false;
	}
	if ($page["ns"] !== 0) {
		echo "not main ns\n";
		return false;
	}
	if ($page["title"] !== $title) {
		$check = "";
		while ($check !== "n") {
			echo "convert title to ".$page["title"]."? (y/n) ";
			$check = strtolower(trim(fgets(STDIN)));
			if ($check === "y") {
				$title = $page["title"];
				break;
			}
		}
	}
	$talktitle = "Talk:".$title;
	$starttimestamp = time();
	$res = cURL($C["wikiapi"]."?".http_build_query(array(
		"action" => "query",
		"prop" => "revisions",
		"format" => "json",
		"rvprop" => "content|timestamp",
		"titles" => $talktitle
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	$page = current($res["query"]["pages"]);
	if (isset($page["missing"])) {
		$basetimestamp = 0;
		$text = "";
	} else {
		$text = $page["revisions"][0]["*"];
		$basetimestamp = $page["revisions"][0]["timestamp"];
	}
	$regdate = preg_quote($date, "/");
	if (preg_match("/{{ *Drv-kept *\| *{$regdate}/", $text)) {
		echo "already tagged\n";
		return false;
	}
	if (trim($result) === "") {
		$result = "完成";
	}
	$add = "{{Drv-kept|$date|$diff|$result}}";
	echo "add ".$add."\n";
	$text = $add."\n".trim($text);

	$summary = $C["summary_prefix"]."[[Special:diff/".$diff."|".$result."]]";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $talktitle,
		"summary" => $summary,
		"text" => $text,
		"token" => $C["edittoken"],
		"starttimestamp" => $starttimestamp,
		"basetimestamp" => $basetimestamp
	);
	echo "edit ".$talktitle." summary=".$summary."\n";

	$check = "";
	while ($check !== "y") {
		echo "continue? (y/n)";
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
		file_put_contents(__DIR__."/out.txt", $text);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		var_dump($res);
		return false;
	} else {
		return true;
	}
}
