<?php

$C["wikiapi"] = "https://zh.wikipedia.org/w/api.php";
$C["user"] = "";
$C["pass"] = "";

$C["nsignore"] = [2, 3];

$C["fetchuser"] = "Xiplus";
$C["timelimit"] = time()-86400*365;

$C["cookiefile"] = __DIR__."/../tmp/AFD-stats-cookie.txt";

$C["votetemplate"] = [
	"nominator" => ["nominator"],
	"fwdcsd" => ["fwdcsd"],
	"d" => ["Vd", "刪除", "删除", "Del", "Removal",
			"Vn", "刪後重建", "删后重建", "重建"], 
	"sd" => ["Vsd", "快速刪除", "快速删除"], 
	// "vsd" => ["Neutral", "中立"], 
	"k" => ["Vk", "保留", "Keep", "VK",
			"Vtk", "暫時保留", "暂时保留"],
	"r" => ["Vr", "重定向"], 
	"sk" => ["Vsk", "快速保留", "Sk", "Speedy keep", "Speedy_keep"], 
	"merge" => ["Vm", "合併", "合并", "Vmerge"], 
	"m" => ["Vmp", "移動", "移动", "Move to", "Move_to",
			"Userfy", "移动到用户页", "Vmu", "移動到用戶頁", "移動至用戶頁", "迁移到用户页", "遷移到用戶頁"], 
	"vm" => ["Vmd", "移動到詞典", "移动到词典", "Vmt", "移動到辭典", "迁移到词典", "遷移到詞典",
		"Vms", "移動到文庫", "移动到文库", "迁移到文库", "遷移到文庫",
		"Vmb", "移動到教科書", "移动到教科书", "迁移到教科书", "遷移到教科書",
		"Vmq", "移動到語錄", "移动到语录", "迁移到语录", "遷移到語錄",
		"Vmvoy", "移動到導遊", "移动到导游", "迁移到导游", "遷移到導遊"]
	// , 
	// "Comment", "意见", "意見", "Opinion", "有條件支持"
];
$C["voteregex"] = [];
foreach ($C["votetemplate"] as $key => $values) {
	$C["voteregex"] = array_merge($C["voteregex"], $values);
}
$C["voteregex"] = implode("|", $C["voteregex"]);

$C["closecode"] = [
	"ir" => ["ir", "rep", "commons", "ne", "notexist", "nq", "notqualified"],
	"k" => ["k", "kept", "tk", "rr", "cc"],
	"r" => ["r", "cr"],
	"sk" => ["sk"],
	"m" => ["m"],
	"merge" => ["merge"],
	"d" => ["dan", "d", "deleted", "drep", "c", "cv", "copyvio"],
	"sd" => ["sd"],
	"vm" => ["twc", "tws", "twb", "twq", "twvoy", "two"],
	"nc" => ["nc"]
];
