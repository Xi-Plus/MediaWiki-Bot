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

echo "The time now is " . date("Y-m-d H:i:s") . " (UTC)\n";

login("bot");
$edittoken = edittoken();

$recenteditcount = [];
$aufrom = "";
while (true) {
	$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
		"action" => "query",
		"format" => "json",
		"list" => "allusers",
		"aulimit" => "max",
		"aufrom" => $aufrom,
		"auactiveusers" => 1,
	)));
	if ($res === false) {
		exit("fetch page fail\n");
	}
	$res = json_decode($res, true);
	foreach ($res["query"]["allusers"] as $user) {
		$recenteditcount[$user["name"]] = $user["recentactions"];
	}
	if (!isset($res["continue"])) {
		break;
	}
	$aufrom = $res["continue"]["aufrom"];
}
echo count($recenteditcount) . " active users\n";

for ($i = 0; $i < $C["fail_retry"]; $i++) {
	$text = file_get_contents($C["page"]);
	if ($text === false) {
		echo "fetch fail\n";
		continue;
	}

	preg_match_all("/^(\* |: .+?\|)(.+)$/m", $text, $m);
	$out = '{| class="wikitable sortable"
!使用者
!簽名
!狀態
!最後編輯
!30天內編輯
!字數
!位元組
';
	foreach ($m[0] as $key => $temp) {
		$status = $m[1][$key];
		if ($status[0] === "*") {
			$status = "active";
		} else {
			$status = substr($status, 2, -1);
		}
		$sign = $m[2][$key];
		$user = "";
		if (preg_match_all("/\[\[(?:(?:User(?:[ _]talk)?|U|UT|用户|用戶|使用者|用戶對話|用戶討論|用户对话|用户讨论|使用者討論):|(?:Special|特殊):(?:(?:Contributions|Contribs)|(?:用户|用戶|使用者)?(?:贡献|貢獻))\/)\s*([^|\/]+?)\s*[|\/]/i", $sign, $m2)) {
			$user = $m2[1][0];
		}
		$res = cURL($C["wikiapi"] . "?" . http_build_query(array(
			"action" => "query",
			"format" => "json",
			"list" => "usercontribs",
			"uclimit" => "1",
			"ucuser" => $user,
			"ucprop" => "timestamp",
		)));
		if ($res === false) {
			exit("fetch page fail\n");
		}
		$res = json_decode($res, true);
		if (!isset($res["query"])) {
			var_dump($res);
		}
		if (isset($res["query"]["usercontribs"][0])) {
			$time = strtotime($res["query"]["usercontribs"][0]["timestamp"]);
		} else {
			$time = 0;
		}
		$date = date("Y年m月d日", $time) . " (" . $C["day"][date("w", $time)] . ") " . date("H:i", $time) . " (UTC)";
		$recentedit = $recenteditcount[$user] ?? 0;
		$len = mb_strlen($sign);
		$byte = strlen($sign);
		if ($byte > 255) {
			$byte = "{{red|'''" . $byte . "'''}}";
		}
		echo ($key + 1) . "\t" . $user . "\t" . $status . "\t" . $date . "\t" . $recentedit . "\t" . $len . "\t" . $byte . "\n";
		$user = "{{User|" . $user . "}}";
		$out .= '|-
|' . $user . '
| ' . $sign . '
|' . $status . '
|data-sort-value=' . $time . '|' . $date . '
|' . $recentedit . '
|' . $len . '
|' . $byte . '
';
	}
	$out .= '|}';

	$summary = $C["summary_prefix"] . "更新";
	$post = array(
		"action" => "edit",
		"format" => "json",
		"title" => $C["outpage"],
		"summary" => $summary,
		"text" => $out,
		"minor" => "",
		"token" => $edittoken,
	);
	echo "edit " . $C["outpage"] . " summary=" . $summary . "\n";
	if (!$C["test"]) {
		$res = cURL($C["wikiapi"], $post);
	} else {
		$res = false;
		file_put_contents(__DIR__ . "/out.txt", $out);
	}
	$res = json_decode($res, true);
	if (isset($res["error"])) {
		echo "edit fail\n";
		continue;
	}

	break;
}
