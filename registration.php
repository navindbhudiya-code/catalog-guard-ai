<?php
/**
 * CatalogGuard AI — Magento admin module.
 *
 * Registers NavinDBhudiya_CatalogGuard. The Python toolkit lives alongside this
 * file in src/, api/, evals/ — Magento ignores those directories.
 */

declare(strict_types=1);

use Magento\Framework\Component\ComponentRegistrar;

ComponentRegistrar::register(
    ComponentRegistrar::MODULE,
    'NavinDBhudiya_CatalogGuard',
    __DIR__
);
