<?php

function afactions(&$item, $key) {
	$act = [
		'warn' => '{{int:abusefilter-action-warn}}',
		'tag' => '{{int:abusefilter-action-tag}}',
		'disallow' => '{{int:abusefilter-action-disallow}}',
		'throttle' => '{{int:abusefilter-action-throttle}}',
		'blockautopromote' => '{{int:abusefilter-action-blockautopromote}}',
		'block' => '{{int:abusefilter-action-block}}',
	];
	if (isset($act[$item])) {
		$item = $act[$item];
	}
}
