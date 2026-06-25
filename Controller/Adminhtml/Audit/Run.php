<?php
/**
 * "Run Audit" action — proxies to the Python service and returns JSON.
 */

declare(strict_types=1);

namespace NavinDBhudiya\CatalogGuard\Controller\Adminhtml\Audit;

use Magento\Backend\App\Action;
use Magento\Backend\App\Action\Context;
use Magento\Framework\Controller\Result\Json;
use Magento\Framework\Controller\Result\JsonFactory;
use NavinDBhudiya\CatalogGuard\Model\PythonService;
use Psr\Log\LoggerInterface;

class Run extends Action
{
    public const ADMIN_RESOURCE = 'NavinDBhudiya_CatalogGuard::audit';

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
            $summary = $this->service->runAudit();

            return $result->setData(['success' => true, 'summary' => $summary]);
        } catch (\Throwable $e) {
            $this->logger->error('CatalogGuard audit failed: ' . $e->getMessage());

            return $result->setData(['success' => false, 'message' => $e->getMessage()]);
        }
    }
}
