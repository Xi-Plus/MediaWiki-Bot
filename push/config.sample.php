<?php

$C["source"] = [
	"gadgetlocal" => "/home/user/sample/",
	"gadgetgithub" => "https://raw.githubusercontent.com/user/repo/master/"
];

$C["target"] = [
	"sample" => "User:Example/sample/",
	"gadget" => "User:Example/gadget/"
];

$C["web"] = [
	"beta" => [
		"wikiapi" => "https://zh.wikipedia.beta.wmflabs.org/w/api.php",
		"user" => "Example",
		"pass" => "",
		"bot" => false,
		"minor" => true,
		"nocreate" => true,
		"cookiefile" =>__DIR__."/../tmp/push-cookie.txt"
	],
	"zhwp" => [
		"wikiapi" => "https://zh.wikipedia.org/w/api.php",
		"user" => "Example",
		"pass" => "",
		"bot" => false,
		"minor" => true,
		"nocreate" => true,
		"cookiefile" => __DIR__."/../tmp/push-wp-cookie.txt"
	]
];

$C["project"] = [
	"sample" => [
		"source" => [
			"gadgetlocal",
			"gadgetgithub",
		],
		"target" => [
			"sample",
			"gadget"
		],
		"web" => [
			"beta",
			"zhwp"
		],
		"summary" => "deploy new feature",
		"files" => [
			'sample.js' => 'sample.js'
		]
	]
];

$C["User-Agent"] = "";
