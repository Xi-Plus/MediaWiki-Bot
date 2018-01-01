<?php
require(__DIR__."/../config/config.php");
if (!in_array(PHP_SAPI, $C["allowsapi"])) {
	exit("No permission");
}

set_time_limit(600);
date_default_timezone_set('UTC');
$starttime = microtime(true);
@include(__DIR__."/config.php");

$time = time();
echo "The time now is ".date("Y-m-d H:i:s", $time)." (UTC)\n";

$dates = ["-1 month", "-3 months", "-6 months", "-1 year"];
$counts = [1, 10, 100, 500, 1000];
$res = [];
foreach ($dates as $date) {
	$realdate = date("Y-m-d", strtotime($date));
	echo $realdate."\n";
	$url = "https://xtools.wmflabs.org/adminstats/zh.wikipedia.org/".$realdate."?uselang=en";
	$html = file_get_contents($url);
	if ($html === false) {
		exit("fetch fail\n");
	}
	preg_match_all('/<td class="sort-entry--user-groups" data-value="(.*?)">/', $html, $m);
	$isadmin = [];
	foreach ($m[1] as $value) {
		$isadmin []= ($value != "");
	}
	preg_match_all('/<td class="sort-entry--total" data-value="(\d+)">/', $html, $m);
	foreach ($m[1] as $key => $total) {
		if ($isadmin[$key]) {
			foreach ($counts as $count) {
				if ((int)$total < $count) {
					@$res[$count][$date] ++;
				}
			}
		}
	}
}
if (preg_match("/<a href='https:\/\/zh\.wikipedia\.org\/w\/index\.php\?title=Special:ListUsers&amp;creationSort=1&amp;group=sysop' target='_blank'>(\d+)<\/a>/", $html, $m)) {
	$admincount = $m[1]-$C["adminbot"];
} else {
	exit("get admincount fail\n");
}

$out = "==統計==
*更新日期：".date("Y年m月d日", $time)." (".$C["day"][date("w", $time)].") ".date("H:i", $time)." (UTC)
*中文維基管理員：".$admincount."人
*備註：由[https://xtools.wmflabs.org/adminstats/zh.wikipedia.org XTools]協助統計，只計算刪除、封禁、保護、匯入、權限，因此可能與實際情況有誤差。

===沒有作出管理方面行為的管理員===
*一年：".$res[1]["-1 year"]."人（".round(100*$res[1]["-1 year"]/$admincount, 1)."%）
*半年：".$res[1]["-6 months"]."人（".round(100*$res[1]["-6 months"]/$admincount, 1)."%）
*三個月：".$res[1]["-3 months"]."人（".round(100*$res[1]["-3 months"]/$admincount, 1)."%）
*一個月：".$res[1]["-1 month"]."人（".round(100*$res[1]["-1 month"]/$admincount, 1)."%）

===管理方面行為次數少於10次===
*一年：".$res[10]["-1 year"]."人（".round(100*$res[10]["-1 year"]/$admincount, 1)."%）
*半年：".$res[10]["-6 months"]."人（".round(100*$res[10]["-6 months"]/$admincount, 1)."%）
*三個月：".$res[10]["-3 months"]."人（".round(100*$res[10]["-3 months"]/$admincount, 1)."%）
*一個月：".$res[10]["-1 month"]."人（".round(100*$res[10]["-1 month"]/$admincount, 1)."%）

===管理方面行為次數少於100次===
*一年：".$res[100]["-1 year"]."人（".round(100*$res[100]["-1 year"]/$admincount, 1)."%）
*半年：".$res[100]["-6 months"]."人（".round(100*$res[100]["-6 months"]/$admincount, 1)."%）
*三個月：".$res[100]["-3 months"]."人（".round(100*$res[100]["-3 months"]/$admincount, 1)."%）

===管理方面行為次數少於500次===
*一年：".$res[500]["-1 year"]."人（".round(100*$res[500]["-1 year"]/$admincount, 1)."%）
*半年：".$res[500]["-6 months"]."人（".round(100*$res[500]["-6 months"]/$admincount, 1)."%）
*三個月：".$res[500]["-3 months"]."人（".round(100*$res[500]["-3 months"]/$admincount, 1)."%）";

echo $out."\n";

$spendtime = (microtime(true)-$starttime);
echo "spend ".$spendtime." s.\n";
