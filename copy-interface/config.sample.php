<?php

$C["target"] = [
	"zhwp" => [
		"wikiapi" => "https://zh.wikipedia.org/w/api.php",
		"user" => "Example",
		"pass" => "",
		"copylist" => [
			"hans" => [
				["/zh-hans", "/zh-cn"],
				["/zh-hans", "/zh-sg"],
			],
			"hant" => [
				["/zh-hant", "/zh-hk"],
				["/zh-hant", "/zh-mo"],
				["/zh-hant", "/zh-tw"],
			],
			"hans2zh" => [
				["/zh-hans", "/zh"],
				["/zh-hans", ""],
			],
			"hant2zh" => [
				["/zh-hant", "/zh"],
				["/zh-hant", ""],
			],
		],
		"bot" => false,
		"cookiefile" => __DIR__ . "/../tmp/copy-interface-zhwp-cookie.txt",
	],
];

$C["summary_prefix"] = "";

$C["User-Agent"] = "";
