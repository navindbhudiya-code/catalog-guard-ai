<?php
/**
 * Apply/Rollback action bar shown above the Review Fixes grid.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Block\Adminhtml\Review;

use Magento\Backend\Block\Template;

class Actions extends Template
{
    public function getApplyUrl(): string
    {
        return $this->getUrl('catalogguard/review/apply');
    }

    public function getRollbackUrl(): string
    {
        return $this->getUrl('catalogguard/review/rollback');
    }
}
