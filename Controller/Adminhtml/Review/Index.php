<?php
/**
 * Renders the "Review Fixes" admin grid.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\View\Result\Page;
use Magento\Framework\View\Result\PageFactory;

class Index extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::review';

    public function __construct(
        Context $context,
        private readonly PageFactory $resultPageFactory
    ) {
        parent::__construct($context);
    }

    public function execute(): Page
    {
        $resultPage = $this->resultPageFactory->create();
        $resultPage->setActiveMenu('NavinDBhudiya_CatalogGuard::review');
        $resultPage->getConfig()->getTitle()->prepend(__('Review Fixes'));

        return $resultPage;
    }
}
