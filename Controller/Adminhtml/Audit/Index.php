<?php
/**
 * Renders the CatalogGuard admin page (latest audit + Run Audit button).
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Audit;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\View\Result\Page;
use Magento\Framework\View\Result\PageFactory;

class Index extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::audit';

    public function __construct(
        Context $context,
        private readonly PageFactory $resultPageFactory
    ) {
        parent::__construct($context);
    }

    public function execute(): Page
    {
        $resultPage = $this->resultPageFactory->create();
        $resultPage->setActiveMenu(self::ADMIN_RESOURCE);
        $resultPage->getConfig()->getTitle()->prepend(__('CatalogGuard AI'));

        return $resultPage;
    }
}
