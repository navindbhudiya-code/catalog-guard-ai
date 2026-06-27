<?php
/**
 * "Generate Fixes" — runs an audit + proposal generation on the Python service
 * and points the admin at the Review Fixes queue.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Review;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\Controller\Result\Json;
use Magento\Framework\Controller\Result\JsonFactory;
use NavinDBhudiya\CatalogGuard\Model\PythonService;
use Psr\Log\LoggerInterface;

class Generate extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::review';

    public function __construct(
        Context $context,
        private readonly JsonFactory $resultJsonFactory,
        private readonly PythonService $service,
        private readonly LoggerInterface $logger
    ) {
        parent::__construct($context);
    }

    public function execute(): Json
    {
        $result = $this->resultJsonFactory->create();

        try {
            $generated = $this->service->generateProposals();

            return $result->setData([
                'success' => true,
                'generated' => $generated,
                'redirect' => $this->getUrl('catalogguard/review/index'),
            ]);
        } catch (\Throwable $e) {
            $this->logger->error('CatalogGuard generate-fixes failed: ' . $e->getMessage());

            return $result->setData(['success' => false, 'message' => $e->getMessage()]);
        }
    }
}
