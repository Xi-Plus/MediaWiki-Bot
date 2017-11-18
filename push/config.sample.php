<?php

$C["target"] = [
	"beta" => [
		"wikiapi" => "https://zh.wikipedia.beta.wmflabs.org/w/api.php",
		"user" => "Example",
		"pass" => "",
		"bot" => false,
		"minor" => true,
		"cookiefile" =>__DIR__."/../tmp/push-cookie.txt",
		"remoteprefix" => "User:Example/sample/"
	],
	"zhwp" => [
		"wikiapi" => "https://zh.wikipedia.org/w/api.php",
		"user" => "Example",
		"pass" => "",
		"bot" => false,
		"minor" => true,
		"cookiefile" => __DIR__."/../tmp/push-wp-cookie.txt",
		"remoteprefix" => "User:Example/sample/"
	]
];

$C["summary_prefix"] = "push";

$C["localprefix"] = "/home/user/sample/";
$C["githubprefix"] = "https://raw.githubusercontent.com/user/repo/";
$C["list"] = [
	"sample.js" => "sample.js"
];

$C["User-Agent"] = "";
